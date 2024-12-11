from django.db import models
from django.contrib.auth.models import User
from django.utils.timezone import now


class Message(models.Model):
    sender_email = models.EmailField()
    recipient_email = models.EmailField()
    sender_model = models.CharField(max_length=50)
    recipient_model = models.CharField(max_length=50)
    subject = models.CharField(max_length=255, blank=True, null=True)
    content = models.TextField(blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    attachments = models.ManyToManyField('MessageAttachment', related_name='messages', blank=True)

    def __str__(self):
        return f"Message from {self.sender_email} to {self.recipient_email} on {self.timestamp}"

class MessageAttachment(models.Model):
    file = models.FileField(upload_to='attachments/%Y/%m/%d/')
    original_name = models.CharField(max_length=255)
    file_type = models.CharField(max_length=50)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Attachment {self.original_name} uploaded on {self.uploaded_at}"


class OnlineStatus(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="online_status")
    is_online = models.BooleanField(default=False)
    last_seen = models.DateTimeField(default=now)

    def __str__(self):
        return f"{self.user.username} - {'Online' if self.is_online else 'Offline'}"

