from django.db import models
from Authentication.models import CustomUser


class Notifications(models.Model):
    sender = models.ForeignKey(CustomUser,on_delete=models.CASCADE,related_name='sender_notifications',null=True)
    user = models.ForeignKey( CustomUser, on_delete=models.CASCADE,related_name='reciever_notifications')
    detail = models.CharField("detail", max_length=250,blank=True,null=True )
    read = models.BooleanField(default=False)
    timestamp = models.DateTimeField(auto_now_add=True)
    notification_type = models.CharField(max_length=200, null=True)
    def __str__(self):
        return self.detail