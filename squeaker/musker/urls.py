from django.urls import path
from django.shortcuts import redirect
from . import views

# Redirect root URL to login page
def root_redirect(request):
    return redirect('login')

urlpatterns = [
    # Root
    path('', root_redirect),

    # Authentication
    path('login/', views.login_user, name='login'),
    path('register/', views.register_user, name='register'),
    path('logout/', views.logout_user, name='logout'),

    # Home
    path('home/', views.home, name='home'),

    # Profiles
    path('profile_list/', views.profile_list, name='profile_list'),
    path('profile/<int:pk>/', views.profile, name='profile'),
    path('profile/edit/', views.edit_profile, name='edit_profile'),

    # Meeps
    path('meep_like/<int:pk>/', views.meep_like, name='meep_like'),
    path('meep_show/<int:pk>/', views.meep_show, name='meep_show'),
    path('meep/<int:meep_id>/comment/', views.meep_comment, name='meep_comment'),
    path('meep_share/<int:pk>/', views.meep_share, name='meep_share'),

    # Explore / Hashtags
    path('explore/', views.explore, name='explore'),
    path('hashtag/<str:hashtag_name>/', views.hashtag_view, name='hashtag'),

    # Notifications
    path('notifications/', views.notifications, name='notifications'),
    path('notifications/<int:notification_id>/read/', views.mark_notification_read, name='mark_notification_read'),
    path('notifications/unread-count/', views.get_unread_count, name='unread_count'),

    # Messaging
    path('messages/', views.messages_view, name='messages'),
    path('messages/<int:user_id>/', views.conversation_detail, name='conversation_detail'),
    path('messages/send/', views.send_message, name='send_message'),
    path('messages/get/<int:user_id>/', views.get_new_messages, name='get_new_messages'),
    path('messages/start/<int:user_id>/', views.start_conversation, name='start_conversation'),
    path('chat/', views.chatbot_view, name='chatbot'),
    path('api/chat/', views.chat_api, name='chat_api'),
]
