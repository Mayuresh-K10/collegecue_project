from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('api/search/', views.search_user, name='search_user'),
    path('api/send_message/', views.send_chat, name='send_message'),
    path('api/get_messages/', views.get_messages, name='get_messages'),
    path('api/inbox/', views.inbox, name='inbox'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
