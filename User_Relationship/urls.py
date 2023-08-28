from django.urls import path
from .views import *
urlpatterns = [
    path('make-post/', MakePosts.as_view(), name='make-post'),
    path('edit-post/<int:post_id>/', EditPost.as_view(), name='edit-post'),
    path('delete-post/<int:post_id>/', DeletePosts.as_view(), name='delete-post'),
    path('react-post/<int:post_id>/', LikeOrUnlike.as_view(), name='like-post'),
    path('make-comment/<int:post_id>/', MakeComment.as_view(), name='make-comment'),
    path('repost/<int:post_id>/', SharePost.as_view(), name='repost'),
    path('users/follow-toggle/<str:username>', FollowOrUnfollow.as_view(), name='follow'),
    path('users/followers/', ListFollowersAndFollowing.as_view(), name='list-followers'),
    path('groups/create/', CreateGroup.as_view(), name='create-group'),
    path('groups/<int:group_id>/manage/', ManageGroup.as_view(), name='manage-group'),
    path('groups/<int:group_id>/join/', JoinGroup.as_view(), name='join-group'),
    path('groups/<int:group_id>/leave/', LeaveGroup.as_view(), name='leave-group'),
    path('search/', Search.as_view(), name='search'),
    path('timeline/', GetPosts.as_view(), name='timeline'),
    path('trending-posts/', GetTrendingPosts.as_view(), name='trending-posts'),

]