from .models import UserRelationship,Groups
from Authentication.models import CustomUser,Privacy
from rest_framework.views import APIView
from django.http import JsonResponse
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.core.cache import cache
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from .models import Posts,Comments
from django.db.models import Q,F,Count
import cloudinary
from rest_framework import status
from .signals import get_new_followers,get_new_comments,like_a_post,like_a_comment
from helpers.utils import RecommendationAlgorithm
from datetime import datetime


class MakePosts(APIView):
    def upload_file(self, request, file):
        if file:
            try:
                resource_type = 'image' if file.content_type.startswith('image') else 'video'
                cloudinary_response = cloudinary.uploader.upload(file, resource_type=resource_type)
                file_url = cloudinary_response['secure_url']
                public_id = cloudinary_response['public_id']
            except cloudinary.exceptions.Error as e:
                return Response({'detail': 'Error uploading file'}, status=status.HTTP_400_BAD_REQUEST)
        else:
            file_url = None
            public_id = None
        
        context = {
            "file_url": file_url,
            "public_id": public_id
        }
        return context
    
    def post(self, request, *args, **kwargs):
        user = request.user
        content = request.data.get('content')
        file_upload = request.FILES.get('file')
        post_privacy  = request .data.get('post_privacy',Privacy.default_choice)
        print(Privacy.privacy_choices)
        valid_privacy_choices = [choice[0] for choice in Privacy.privacy_choices]
        if post_privacy not in valid_privacy_choices:
            return Response({"detail": f"Invalid choice. Allowed values: {', '.join(valid_privacy_choices)}"}, status=status.HTTP_400_BAD_REQUEST)
        if file_upload:
            # Use ImageField and FileField validation
            if file_upload.content_type.startswith('image') or file_upload.content_type.startswith('video'):
                data = self.upload_file(request, file_upload)
                file_url = data.get('file_url')
                public_id = data.get('public_id')
                print(file_upload)
                Posts.objects.create(file=file_url, content=content, user=user,post_privacy=post_privacy)
                return Response({'detail': 'Post created successfully', 'public_id': public_id}, status=status.HTTP_200_OK)
            else:
                return Response({'detail': 'Invalid file type'}, status=status.HTTP_400_BAD_REQUEST)
        else:
            Posts.objects.create(content=content, user=user,post_privacy=post_privacy)
            return Response({'detail': 'Post created successfully'}, status=status.HTTP_200_OK)

class EditPost(APIView):      
    def put(self, request, post_id, *args, **kwargs):
        user = request.user
        content = request.data.get('content')
        file_upload = request.FILES.get('file')
        post_privacy  = request .data.get('post_privacy')
        post = get_object_or_404(Posts,id=post_id)
        
        if post.user != user:
            return Response({'detail': 'You don\'t have permission to edit this post.'}, status=status.HTTP_403_FORBIDDEN)
         
        post_privacy  = request .data.get('post_privacy',Privacy.default_choice)
        print(Privacy.privacy_choices)
        valid_privacy_choices = [choice[0] for choice in Privacy.privacy_choices]
        if post_privacy not in valid_privacy_choices:
            return Response({"detail": f"Invalid choice. Allowed values: {', '.join(valid_privacy_choices)}"}, status=status.HTTP_400_BAD_REQUEST)
        else:
            post.post_privacy = post_privacy
            post.save()
        if file_upload:
            if file_upload.content_type.startswith('image') or file_upload.content_type.startswith('video'):
                file_object = MakePosts
                data = file_object.upload_file(self,request, file_upload)
                file_url = data.get('file_url')
                public_id = data.get('public_id')
                post.file = file_url
                post.save()
                
            else:
                return Response({'detail': 'Invalid file type'}, status=status.HTTP_400_BAD_REQUEST)
        else:
            public_id=None
        if content:
            post.content = content
            post.save()
            return Response({'detail': 'Post updated successfully', 'public_id': public_id}, status=status.HTTP_200_OK)
        
class DeletePosts(APIView):
    def delete(self, request, post_id, *args, **kwargs):
        user = request.user
        post = get_object_or_404(Posts,id=post_id)
        if post.user != user:
            return Response({'detail': 'You don\'t have permission to edit this post.'}, status=status.HTTP_403_FORBIDDEN)   
        post.delete()
        return Response({'details':'posts deleted successfully'},status=status.HTTP_200_OK)
    


class SharePost(APIView):
    def post(self, request, post_id, *args, **kwargs):
        user = request.user
        original_post = get_object_or_404(Posts, id=post_id)
        
        new_post = Posts.objects.create(
            user=user,
            content=original_post.content,
            file = original_post.file,
            original_post=original_post 
        )
        
        return Response({'detail': 'Post shared successfully'}, status=status.HTTP_201_CREATED)

    
class LikeOrUnlike(APIView):
    def post(self,request,post_id):
        user = request.user
        post = get_object_or_404(Posts,id=post_id)
        
        if user in post.likes.all():
            post.likes.remove(user)
            response = 'Post unliked!'
        else:
            post.likes.add(user)
            response = 'Post liked!'
        context = {
            'message':response,
            'count':post.likes.count()
        }
        return Response({'detail':context},status=status.HTTP_200_OK)
    
        
class MakeComment(APIView):
    def post(self, request, post_id, *args, **kwargs):
        user = request.user
        comment_text = request.data.get('comment')
        file_upload = request.FILES.get('file')
        parent_comment_id = request.data.get('parent_comment_id')
        post=get_object_or_404(Posts,id=post_id)
        if file_upload:
            file_url = MakePosts
            data = file_url.upload_file(self,request, file_upload)
            file_url = data.get('file_url')
            public_id = data.get('public_id')
        else:
            file_url = None
            public_id =None

        comment = Comments.objects.create(
            comment_user=user,
            comment=comment_text,
            file=file_url,
            post = post 
        )
        
        parent_comment = None
        if parent_comment_id:
            try:
                parent_comment = Comments.objects.get(id=parent_comment_id)
                comment.parent_comment = parent_comment
                comment.save()
            except Comments.DoesNotExist:
                pass
        return Response({'detail': 'Comment created successfully', 'public_id': public_id}, status=status.HTTP_201_CREATED)


        
    


    


# class Timeline(APIView):
#     def get(self, request, *args, **kwargs):
#         user_id = request.user.id
#         followed_users_ids = UserRelationship.objects.filter(follower=user_id).values_list('followed_id', flat=True)
#         timeline_posts = Posts.objects.filter(Q(user=user_id) | Q(user__in=followed_users_ids)).prefetch_related('comments', 'likes').values_list
#         timeline_posts = timeline_posts.order_by('-created_at')

#         recommendation_algorithm = RecommendationAlgorithm()
#         recommended_posts = recommendation_algorithm.get_content_based_filtered_posts(timeline_posts, k=5)

#         timeline_posts |= recommended_posts


#         return JsonResponse({'detail': list(timeline_posts)})



class FollowOrUnfollow(APIView):
    def post(self, request, username, *args, **kwargs):
        follower_user = request.user
        following_user = get_object_or_404(CustomUser, username=username)
        
        if follower_user == following_user:
            return Response({'detail': "You can't follow/unfollow yourself."}, status=status.HTTP_400_BAD_REQUEST)
        
        relationship, created = UserRelationship.objects.get_or_create(
            follower=follower_user,
            following=following_user
        )
        if created:
            return Response({'detail': f'You are now following {following_user.username}'}, status=status.HTTP_200_OK)
        else:
            relationship.delete()
            return Response({'detail': f'You have unfollowed {following_user.username}'}, status=status.HTTP_200_OK)

class ListFollowersAndFollowing(APIView):
    def get(self, request, *args, **kwargs):
        username = request.GET.get('username')
        user = get_object_or_404(CustomUser, username=username)
        
        followers = user.follower_relationships.filter().values(username=F('follower__username'),
        full_name = F('follower__full_name'),profile_picture = F('follower__profile_picture')
        )
        followers_count = followers.count()
        
        following = user.following_relationships.filter().values(username=F('following__username'),
        full_name = F('following__full_name'),profile_picture = F('following__profile_picture')
        )
        following_count = following.count()
        
        data = {
            'followers_count': followers_count,
            'following_count': following_count,
            'followers': list(followers),
            'following': list(following)
        }
        
        return Response({'details': data}, status=status.HTTP_200_OK)



class ListFollowing(APIView):
    def get(self, request,*args, **kwargs):
        username = request.GET.get('username')
        user = get_object_or_404(CustomUser, username=username)
        following = user.following_relationships.all()
        following_usernames = [follow.following.username for follow in following]
        return Response({'following': following_usernames}, status=status.HTTP_200_OK)



class CreateGroup(APIView):
    def post(self, request, *args, **kwargs):
        name = request.data.get('name')
        admin = request.user
        date = datetime.now()
        group = Groups.objects.create(name=name, admin=admin,joined_at = date)
        group.members.add(admin)  
        
        return Response({'detail': 'Group created successfully', 'group_id': group.id}, status=status.HTTP_201_CREATED)

class ManageGroup(APIView):
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
    def post(self, request, group_id, *args, **kwargs):
        group = get_object_or_404(Groups, id=group_id)
        user = request.user

        if group.members.filter(id=user.id).exists():
            return Response({'detail': 'You are already a member of this group'}, status=status.HTTP_400_BAD_REQUEST)
        group.members.add(user)
        return Response({'detail': f'You have joined {group.name}'}, status=status.HTTP_200_OK)

class LeaveGroup(APIView):
    def post(self, request, group_id, *args, **kwargs):
        group = get_object_or_404(Groups, id=group_id)
        user = request.user
        
        if group.members.filter(id=user.id).exists():
            group.members.remove(user)
            return Response({'detail': f'You have left the {group.name}'}, status=status.HTTP_200_OK)
        else:
            return Response({'detail': 'You are not a member of this group'}, status=status.HTTP_400_BAD_REQUEST)
        

class Search(APIView):
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
        post_results = [{'type': 'post', 'id': post.id, 'content': post.content,'file':post.file} for post in (public_posts | follower_posts)]
        
        # Search for public groups
        public_groups = Groups.objects.filter(name__icontains=query)
        group_results = [{'type': 'group', 'id': group.id, 'name': group.name} for group in public_groups]
        
        all_results = user_results + post_results + group_results
        
        return Response({'detail': all_results}, status=status.HTTP_200_OK)
    

class GetPosts(APIView):
    def get(self,request,*args, **kwargs):
        user = request.user
        follower_posts = Posts.objects.filter(Q(post_privacy='public') | Q(post_privacy='followers') & Q(user__follower_relationships__follower=request.user)).annotate(
            like_count=Count('likes'),comments_count=Count('comments'),reposts_count=Count('reposts')
        ).order_by('created_at')
        post_list = []
        for post in follower_posts:
            post_data = {
                'id': post.id,
                'content': post.content,
                'file':post.file,
                'created_at':post.created_at,
                'likes':post.like_count,
                'comments':post.comments_count,
                'reposts':post.reposts_count,
                'user': {
                    'username': post.user.username,
                    'full_name': post.user.full_name
                },
            }
            post_list.append(post_data)
        
        return Response({'detail': post_list}, status=status.HTTP_200_OK)
    
class GetTrendingPosts(APIView):
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
    
    class GetPostsRecommendation(APIView):
        def get(self,request,*args, **kwargs):
            user = request.user
            








