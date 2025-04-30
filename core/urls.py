from django.urls import path, re_path
from . import views

app_name = 'core'

urlpatterns = [
    path('', views.home_feed, name='home'),
    path('explore/', views.explore, name='explore'),
    path('notifications/', views.notifications, name='notifications'),
    re_path(r'^messages/(?:(?P<conversation_id>\d+)/)?$', views.messages_view, name='messages'),
    path('messages/new/', views.create_conversation, name='create_conversation'),
    path('messages/search-users/', views.search_users, name='search_users'),
    path('messages/<int:conversation_id>/send/', views.send_message, name='send_message'),
    path('messages/<int:conversation_id>/updates/', views.get_conversation_updates, name='conversation_updates'),
    path('messages/<int:conversation_id>/mark-read/', views.mark_as_read, name='mark_messages_read'),
    path('messages/<int:conversation_id>/typing/', views.update_typing_status, name='update_typing_status'),
    path('messages/message/<int:message_id>/react/', views.react_to_message, name='react_to_message'),
    path('profile/<str:username>/', views.profile, name='profile'),
    path('profile/<str:username>/edit/', views.edit_profile, name='edit_profile'),
    path('profile/<str:username>/settings/', views.profile_settings, name='profile_settings'),
    path('settings/', views.settings, name='settings'),
    path('profile/update-picture/', views.update_profile_picture, name='update_profile_picture'),
    path('post/create/', views.create_post, name='create_post'),
    path('post/<int:post_id>/', views.post_detail, name='post_detail'),
    path('post/<int:post_id>/edit/', views.edit_post, name='edit_post'),
    path('delete-post/<int:post_id>/', views.delete_post, name='delete_post'),
    path('post/<int:post_id>/like/', views.like_post, name='like_post'),
    path('post/<int:post_id>/comment/', views.add_comment, name='add_comment'),
    path('post/<int:post_id>/save/', views.save_post, name='save_post'),
    path('post/<int:post_id>/share/', views.share_post, name='share_post'),
    path('follow/<str:username>/', views.follow_user, name='follow_user'),
    path('unfollow/<str:username>/', views.unfollow_user, name='unfollow_user'),
    path('toggle-theme/', views.toggle_theme, name='toggle_theme'),
] 