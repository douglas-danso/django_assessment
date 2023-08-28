# Import necessary modules and classes
from .models import UserRelationship, Groups
from Authentication.models import CustomUser, Privacy
from rest_framework.views import APIView
from django.http import JsonResponse
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.core.cache import cache
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from .models import Posts, Comments
from django.db.models import Q, F, Count
import cloudinary
from rest_framework import status
from .tasks import *
from helpers.utils import RecommendationAlgorithm
from datetime import datetime
from Authentication.tasks import delete_cloudinary_file_async
from tempfile import NamedTemporaryFile

# API view to create posts
class MakePosts(APIView):
    authentication_classes = (JWTAuthentication,)
    permission_classes = (IsAuthenticated,)

    def post(self, request, *args, **kwargs):
        user = request.user
        content = request.data.get('content')
        file_upload = request.FILES.get('file')
        post_privacy = request.data.get('post_privacy', Privacy.default_choice)

        # Validate post privacy choice
        valid_privacy_choices = [choice[0] for choice in Privacy.privacy_choices]
        if post_privacy not in valid_privacy_choices:
            return Response({"detail": f"Invalid choice. Allowed values: {', '.join(valid_privacy_choices)}"}, status=status.HTTP_400_BAD_REQUEST)
        
        # Check for file upload
        if file_upload:
            if file_upload.content_type.startswith('image') or file_upload.content_type.startswith('video'):
                resource_type = 'image' if file_upload.content_type.startswith('image') else 'video'
                with NamedTemporaryFile(delete=False) as temp_file:
                    for chunk in file_upload.chunks():
                        temp_file.write(chunk)
                    temp_file_path = temp_file.name
                
                # Start the Celery task asynchronously
                async_upload_file.delay(temp_file_path, content, post_privacy, user.id, resource_type)
            else:
                return Response({'detail': 'Invalid file type'}, status=status.HTTP_400_BAD_REQUEST)
        else:
            # Create a post without file
            Posts.objects.create(content=content, user=user, post_privacy=post_privacy)
            return Response({'detail': 'Post created successfully'}, status=status.HTTP_200_OK)

# API view to edit posts
class EditPost(APIView): 
    authentication_classes = (JWTAuthentication,)
    permission_classes = (IsAuthenticated,)

    def put(self, request, post_id, *args, **kwargs):
        user = request.user
        content = request.data.get('content')
        file_upload = request.FILES.get('file')
        post_privacy = request.data.get('post_privacy')
        post = get_object_or_404(Posts, id=post_id)
        
        # Check user permission
        if post.user != user:
            return Response({'detail': 'You don\'t have permission to edit this post.'}, status=status.HTTP_403_FORBIDDEN)
         
        # Validate post privacy choice
        valid_privacy_choices = [choice[0] for choice in Privacy.privacy_choices]
        if post_privacy not in valid_privacy_choices:
            return Response({"detail": f"Invalid choice. Allowed values: {', '.join(valid_privacy_choices)}"}, status=status.HTTP_400_BAD_REQUEST)
        else:
            post.post_privacy = post_privacy
            post.save()
            
        if file_upload:
            if file_upload.content_type.startswith('image') or file_upload.content_type.startswith('video'):
                file_url = post.file
                delete_cloudinary_file_async.delay(file_url)
                resource_type = 'image' if file_upload.content_type.startswith('image') else 'video'
                # Save the uploaded file temporarily
                with NamedTemporaryFile(delete=False) as temp_file:
                    for chunk in file_upload.chunks():
                        temp_file.write(chunk)
                    temp_file_path = temp_file.name
                
                # Start the Celery task asynchronously
                async_upload_file.delay(temp_file_path, content, post_privacy, user.id, resource_type)
            else:
                return Response({'detail': 'Invalid file type'}, status=status.HTTP_400_BAD_REQUEST)
            
        if content:
            post.content = content
            post.save()
            
        return Response({'detail': 'Post updated successfully'}, status=status.HTTP_200_OK)

# API view to delete posts
class DeletePosts(APIView):
    authentication_classes = (JWTAuthentication,)
    permission_classes = (IsAuthenticated,)

    def delete(self, request, post_id, *args, **kwargs):
        user = request.user
        post = get_object_or_404(Posts, id=post_id)
        
        # Check user permission
        if post.user != user:
            return Response({'detail': 'You don\'t have permission to delete this post.'}, status=status.HTTP_403_FORBIDDEN)
        
        # Delete associated file from Cloudinary
        if post.file:
            file_url = post.file
            delete_cloudinary_file_async.delay(file_url)   
        post.delete()
        return Response({'details': 'Post deleted successfully'}, status=status.HTTP_200_OK)

# API view to share posts
class SharePost(APIView):
    authentication_classes = (JWTAuthentication,)
    permission_classes = (IsAuthenticated,)

    def post(self, request, post_id, *args, **kwargs):
        user = request.user
        original_post = get_object_or_404(Posts, id=post_id)
        
        # Create a new post based on the original post
        new_post = Posts.objects.create(
            user=user,
            content=original_post.content,
            file=original_post.file,
            original_post=original_post 
        )
        user_email = original_post.user.email
        send_notification_email.delay(user_email, "repost", original_post.content)
        return Response({'detail': 'Post shared successfully'}, status=status.HTTP_201_CREATED)

# API view to like or unlike posts
class LikeOrUnlike(APIView):
    authentication_classes = (JWTAuthentication,)
    permission_classes = (IsAuthenticated,)

    def post(self, request, post_id):
        user = request.user
        post = get_object_or_404(Posts, id=post_id)
        
        # Toggle like/unlike for the post
        if user in post.likes.all():
            post.likes.remove(user)
            response = 'Post unliked!'
        else:
            post.likes.add(user)
            response = 'Post liked!'
            user_email = post.user.email
            send_notification_email.delay(user_email, "like", post.content)
        context = {
            'message': response,
            'count': post.likes.count()
        }
        return Response({'detail': context}, status=status.HTTP_200_OK)

# API view to create comments on posts
class MakeComment(APIView):
    authentication_classes = (JWTAuthentication,)
    permission_classes = (IsAuthenticated,)

    def post(self, request, post_id, *args, **kwargs):
        user = request.user
        comment_text = request.data.get('comment')
        file_upload = request.FILES.get('file')
        parent_comment_id = request.data.get('parent_comment_id')
        post = get_object_or_404(Posts, id=post_id)
        
        # Check file upload and validate file type
        if file_upload:
            if file_upload.content_type.startswith('image') or file_upload.content_type.startswith('video'):
                file_url = post.file
                delete_cloudinary_file_async.delay(file_url)
                resource_type = 'image' if file_upload.content_type.startswith('image') else 'video'
                # Save the uploaded file temporarily
                with NamedTemporaryFile(delete=False) as temp_file:
                    for chunk in file_upload.chunks():
                        temp_file.write(chunk)
                    temp_file_path = temp_file.name
                
                # Start the Celery task asynchronously
                async_upload_file_comment.delay(temp_file_path, comment_text, user.id, resource_type, post_id, parent_comment_id)
                user_email = post.user.email
                send_notification_email.delay(user_email, "comment", post.content)
                return Response({'detail': 'Comment created successfully'}, status=status.HTTP_201_CREATED)
            else:
                return Response({'detail': 'Invalid file type'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Create a comment without file
        comment = Comments.objects.create(
            comment_user=user,
            comment=comment_text,
            post=post 
        )
        
        # Handle parent comments
        parent_comment = None
        if parent_comment_id:
            try:
                parent_comment = Comments.objects.get(id=parent_comment_id)
                comment.parent_comment = parent_comment
                comment.save()
            except Comments.DoesNotExist:
                pass
        user_email = post.user.email
        send_notification_email.delay(user_email, "comment", post.content)
        return Response({'detail': 'Comment created successfully'}, status=status.HTTP_201_CREATED)

# API view to follow or unfollow users
class FollowOrUnfollow(APIView):
    authentication_classes = (JWTAuthentication,)
    permission_classes = (IsAuthenticated,)

    def post(self, request, username, *args, **kwargs):
        follower_user = request.user
        following_user = get_object_or_404(CustomUser, username=username)
        
        # Check if the follower is trying to follow themselves
        if follower_user == following_user:
            return Response({'detail': "You can't follow/unfollow yourself."}, status=status.HTTP_400_BAD_REQUEST)
        
        # Create or delete relationship based on whether already following
        relationship, created = UserRelationship.objects.get_or_create(
            follower=follower_user,
            following=following_user
        )
        if created:
            user_email = following_user.email
            follower_name = follower_user.full_name  
            send_follow_notification_email.delay(user_email, follower_name)
            return Response({'detail': f'You are now following {following_user.username}'}, status=status.HTTP_200_OK)
        else:
            relationship.delete()
            return Response({'detail': f'You have unfollowed {following_user.username}'}, status=status.HTTP_200_OK)

# API view to list followers and following of a user
class ListFollowersAndFollowing(APIView):
    authentication_classes = (JWTAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        username = request.GET.get('username')
        user = get_object_or_404(CustomUser, username=username)
        
        # Retrieve followers and following relationships
        followers = user.follower_relationships.filter().values(
            username=F('follower__username'),
            full_name=F('follower__full_name'),
            profile_picture=F('follower__profile_picture')
        )
        followers_count = followers.count()
        
        following = user.following_relationships.filter().values(
            username=F('following__username'),
            full_name=F('following__full_name'),
            profile_picture=F('following__profile_picture')
        )
        following_count = following.count()
        
        data = {
            'followers_count': followers_count,
            'following_count': following_count,
            'followers': list(followers),
            'following': list(following)
        }
        
        return Response({'details': data}, status=status.HTTP_200_OK)
class CreateGroup(APIView):
    authentication_classes = (JWTAuthentication,)
    permission_classes = (IsAuthenticated,)
    def post(self, request, *args, **kwargs):
        name = request.data.get('name')
        admin = request.user
        date = datetime.now()
        group = Groups.objects.create(name=name, admin=admin,joined_at = date)
        group.members.add(admin)  
        
        return Response({'detail': 'Group created successfully', 'group_id': group.id}, status=status.HTTP_201_CREATED)

class ManageGroup(APIView):
    authentication_classes = (JWTAuthentication,)
    permission_classes = (IsAuthenticated,)
    def put(self, request, group_id, *args, **kwargs):
        group = get_object_or_404(Groups, id=group_id, admin=request.user)
        new_name = request.data.get('name')
        if new_name:
            group.name = new_name
            group.save()
        
        return Response({'detail': 'Group updated successfully'}, status=status.HTTP_200_OK)

    def delete(self, request, group_id, *args, **kwargs):
        group = get_object_or_404(Groups, id=group_id, admin=request.user)
        group.delete()
        return Response({'detail': 'Group deleted successfully'}, status=status.HTTP_204_NO_CONTENT)

class JoinGroup(APIView):
    authentication_classes = (JWTAuthentication,)
    permission_classes = (IsAuthenticated,)
    def post(self, request, group_id, *args, **kwargs):
        group = get_object_or_404(Groups, id=group_id)
        user = request.user

        if group.members.filter(id=user.id).exists():
            return Response({'detail': 'You are already a member of this group'}, status=status.HTTP_400_BAD_REQUEST)
        group.members.add(user)
        return Response({'detail': f'You have joined {group.name}'}, status=status.HTTP_200_OK)

class LeaveGroup(APIView):
    authentication_classes = (JWTAuthentication,)
    permission_classes = (IsAuthenticated,)
    def post(self, request, group_id, *args, **kwargs):
        group = get_object_or_404(Groups, id=group_id)
        user = request.user
        
        if group.members.filter(id=user.id).exists():
            group.members.remove(user)
            return Response({'detail': f'You have left the {group.name}'}, status=status.HTTP_200_OK)
        else:
            return Response({'detail': 'You are not a member of this group'}, status=status.HTTP_400_BAD_REQUEST)
# API view to search users, posts, and groups
class Search(APIView):
    authentication_classes = (JWTAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        query = request.query_params.get('query', '')
        
        # Search for users based on query and profile privacy
        users = CustomUser.objects.filter(
            (Q(username__icontains=query) | Q(full_name__icontains=query))
            & (Q(profile_privacy='public') | Q(follower_relationships__follower=request.user))
        )
        
        user_results = [{'type': 'user', 'username': user.username, 'full_name': user.full_name} for user in users]
        
        # Search for public posts and posts visible to the user's followers
        public_posts = Posts.objects.filter(Q(content__icontains=query) & Q(post_privacy='public'))
        follower_posts = Posts.objects.filter(Q(content__icontains=query) & Q(post_privacy='followers') & Q(user__follower_relationships__follower=request.user))
        post_results = [{'type': 'post', 'id': post.id, 'content': post.content, 'file': post.file} for post in (public_posts | follower_posts)]
        
        # Search for public groups
        public_groups = Groups.objects.filter(name__icontains=query)
        group_results = [{'type': 'group', 'id': group.id, 'name': group.name} for group in public_groups]
        
        all_results = user_results + post_results + group_results
        
        return Response({'detail': all_results}, status=status.HTTP_200_OK)

# API view to get posts
class GetPosts(APIView):
    authentication_classes = (JWTAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        user = request.user
        
        # Retrieve posts based on privacy settings and annotate with counts
        follower_posts = Posts.objects.filter(Q(post_privacy='public') | Q(post_privacy='followers') & Q(user__follower_relationships__follower=request.user)).annotate(
            like_count=Count('likes'), comments_count=Count('comments'), reposts_count=Count('reposts')
        ).order_by('created_at')
        
        post_list = []
        for post in follower_posts:
            post_data = {
                'id': post.id,
                'content': post.content,
                'file': post.file,
                'created_at': post.created_at,
                'likes': post.like_count,
                'comments': post.comments_count,
                'reposts': post.reposts_count,
                'user': {
                    'username': post.user.username,
                    'full_name': post.user.full_name
                },
            }
            post_list.append(post_data)
        
        return Response({'detail': post_list}, status=status.HTTP_200_OK)


    
# API view to get trending posts
class GetTrendingPosts(APIView):
    authentication_classes = (JWTAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        user = request.user
        
        # Annotate each post with its total interaction count
        posts = Posts.objects.filter(Q(post_privacy='public') | Q(post_privacy='followers')).annotate(
            interaction_count=Count('likes') + Count('comments') + Count('reposts')
        ).order_by('-interaction_count')
        
        # Serialize each post to a dictionary
        post_list = []
        for post in posts:
            post_data = {
                'id': post.id,
                'content': post.content,
                'file': post.file,
                'user': {
                    'username': post.user.username,
                    'full_name': post.user.full_name
                },
                'interaction_count': post.interaction_count,
            }
            post_list.append(post_data)
        
        return Response({'posts': post_list}, status=status.HTTP_200_OK)


