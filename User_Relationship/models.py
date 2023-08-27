from django.db import models
from Authentication.models import CustomUser

class UserRelationship(models.Model):
    follower = models.ForeignKey(CustomUser,on_delete=models.CASCADE,related_name='following_relationships')
    following = models.ForeignKey(CustomUser,on_delete=models.CASCADE,related_name='follower_relationships')
    created_at = models.DateTimeField(auto_now_add=True)

class Posts(models.Model):
    user = models.ForeignKey(CustomUser,on_delete=models.CASCADE,related_name='posts')
    content = models.TextField(null=True)
    file = models.CharField(max_length=250,null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    likes = models.ManyToManyField(CustomUser, related_name='liked_posts')
    original_post = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='reposts')

class Comments(models.Model):
    comment_user = models.ForeignKey(CustomUser,on_delete=models.CASCADE,related_name='comments' )
    parent_comment = models.ForeignKey('self', on_delete=models.CASCADE,null=True,blank=True,related_name='replies')
    comment = models.TextField()
    post = models.ForeignKey(Posts,on_delete=models.CASCADE,related_name='comments')
    file = models.CharField(max_length=250,null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    likes = models.ManyToManyField(CustomUser, related_name='liked_comments')

class Groups(models.Model):
    name = models.CharField(max_length=64)
    admin = models.ForeignKey(CustomUser,on_delete=models.CASCADE,related_name='group_admin')
    members = models.ManyToManyField(CustomUser, related_name='members')
    created_at = models.DateTimeField(auto_now_add=True)
    joined_at = models.DateTimeField(auto_now=False)





   