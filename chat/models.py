from django.db import models
from django.contrib.auth.models import User
from django.utils.timezone import now


from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models

class Message(models.Model):
    sender_email = models.EmailField()
    recipient_email = models.EmailField()
    sender_model = models.CharField(max_length=50)  # E.g., 'JobSeeker', 'new_user'
    recipient_model = models.CharField(max_length=50)  # E.g., 'JobSeeker', 'new_user'
    subject = models.CharField(max_length=255, blank=True, null=True)
    content = models.TextField(blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    # Adding many-to-many relation for multiple attachments
    attachments = models.ManyToManyField('MessageAttachment', related_name='messages', blank=True)

    def __str__(self):
        return f"Message from {self.sender_email} to {self.recipient_email} on {self.timestamp}"

class MessageAttachment(models.Model):
    # Store the file
    file = models.FileField(upload_to='attachments/%Y/%m/%d/')
    # Store the file's original name
    original_name = models.CharField(max_length=255)
    # Store the type of file (e.g., pdf, jpg, zip, etc.)
    file_type = models.CharField(max_length=50)
    # Store the timestamp of when the file was uploaded
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Attachment {self.original_name} uploaded on {self.uploaded_at}"


class OnlineStatus(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="online_status")
    is_online = models.BooleanField(default=False)
    last_seen = models.DateTimeField(default=now)

    def __str__(self):
        return f"{self.user.username} - {'Online' if self.is_online else 'Offline'}"

