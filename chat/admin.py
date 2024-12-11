from django.contrib import admin
from .models import Message, MessageAttachment, OnlineStatus

# Register your models here.
admin.site.register(Message)
admin.site.register(MessageAttachment)
admin.site.register(OnlineStatus)
