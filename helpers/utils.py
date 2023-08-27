import jwt
import os
from Authentication.models import CustomUser
from Notification.models import Notifications
from django.db.models import Q
from sklearn.metrics.pairwise import cosine_similarity
from User_Relationship.models import Posts, UserRelationship
from sklearn.feature_extraction.text import TfidfVectorizer
import secrets


# def generate_secret_key():
#     return secrets.token_hex(32)  # 32 bytes = 256 bits

# new_secret = generate_secret_key()

# # Update .env file with new secret key
# with open('.env', 'a') as env_file:
#     env_file.write(f'\nSECRET={new_secret}\n')

# print("New secret key generated and added to .env")

def encode_token(**payload):
    encoded_token = jwt.encode(payload = payload, key=os.getenv('SECRET'), algorithm=os.getenv('ALGORITHM'))
    return encoded_token

def decode_token(encoded_token):
    key = os.getenv('SECRET') 
    algorithm = os.getenv('ALGORITHM')  
    
    try:
        decoded_payload = jwt.decode(encoded_token, key, algorithms=[algorithm])
        return decoded_payload
    except jwt.ExpiredSignatureError:
        return "Token has expired."
    except jwt.InvalidTokenError:
        return "Invalid token."


def get_notifications(user):
    notifications_filter = Q(user_id=user.id, notification_type__contains='user notification')
    # Fetch notifications and related data
    notifications = (
        Notifications.objects
        .filter(notifications_filter)
        .order_by("-id")
        .select_related('user')
        .prefetch_related('user')[:7]
    ).values_list('id', 'sender_id', 'detail', 'read', 'timestamp')

    sender_ids = set(notification[1] for notification in notifications)
    sender = CustomUser.objects.in_bulk(sender_ids)

    notif = []
    for notification in notifications:
        sender_id = notification[1]
        sender = sender.get(sender_id)
        if sender:
            notif.append({
                "id": notification[0],
                "sender_id": sender_id,
                "name": sender.full_name,
                "profile_picture": sender.profile_picture,
                "detail": notification[2],
                "read": notification[3],
                "timestamp": notification[4].isoformat()
            })
    return notif


class RecommendationAlgorithm:
    def get_recommended_posts(self, user_id, k=5):
        # Collaborative Filtering
        user_item_matrix = self.build_user_item_matrix()
        similar_users = self.find_similar_users(user_item_matrix, user_id, k)
        collaborative_posts = self.get_collaborative_filtered_posts(similar_users, user_id)

        # Content-Based Filtering
        user_interacted_posts = Posts.objects.filter(user=user_id)
        content_based_posts = self.get_content_based_filtered_posts(user_interacted_posts, k)

        # Combine Recommendations
        recommended_posts = collaborative_posts | content_based_posts

        return recommended_posts.distinct().order_by('-created_at')[:k]

    def build_user_item_matrix(self):
        users = CustomUser.objects.all()
        posts = Posts.objects.all()
        user_item_matrix = {}

        for user in users:
            user_posts = posts.filter(user=user)
            user_item_matrix[user.id] = {post.id: 0 for post in user_posts}

        return user_item_matrix

    def find_similar_users(self, user_item_matrix, user_id, k):
        target_user = user_item_matrix[user_id]
        similarities = []

        for uid, posts in user_item_matrix.items():
            if uid != user_id:
                similarity = cosine_similarity([list(target_user.values())], [list(posts.values())])[0][0]
                similarities.append((uid, similarity))

        similarities.sort(key=lambda x: x[1], reverse=True)
        similar_users = [uid for uid, _ in similarities[:k]]

        return similar_users

    def get_collaborative_filtered_posts(self, similar_users, user_id):
        followed_users_ids = UserRelationship.objects.filter(follower=user_id).values_list('followed_id', flat=True)
        posts = Posts.objects.filter(Q(user__in=similar_users) | Q(user__in=followed_users_ids))
        return posts

    def get_content_based_filtered_posts(self, user_interacted_posts, k):
        # Extract features from posts (e.g., tags, categories, text content)
        all_posts = Posts.objects.all()
        all_post_texts = [post.post for post in all_posts]

        # Combine user-interacted post text with all post texts
        post_texts = [post.post for post in user_interacted_posts]
        post_texts += all_post_texts

        # Create TF-IDF vectorizer and transform post texts into feature vectors
        vectorizer = TfidfVectorizer()
        feature_vectors = vectorizer.fit_transform(post_texts)

        # Compute similarity between posts based on feature vectors
        similarity_matrix = cosine_similarity(feature_vectors)

        # Get indices of user-interacted posts in the similarity matrix
        interacted_post_indices = [all_posts.index(post) for post in user_interacted_posts]

        # Compute average similarity of user-interacted posts with all other posts
        avg_similarities = similarity_matrix[interacted_post_indices].mean(axis=0)

        # Sort the posts based on average similarity and get top-k similar posts
        top_k_indices = avg_similarities.argsort()[::-1][:k]
        recommended_posts = [all_posts[index] for index in top_k_indices]

        return recommended_posts


    