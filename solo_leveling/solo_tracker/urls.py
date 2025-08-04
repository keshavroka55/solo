from django.urls import path
from . import views
from django.contrib.auth.views import LoginView


app_name = 'solo_tracker'

urlpatterns = [
    path('', views.home, name='home'),
    path('login/',LoginView.as_view(template_name ='registration/login.html'), name='login'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('complete-quest/<int:quest_id>/', views.complete_quest, name='complete_quest'),
    path('leaderboard/', views.leaderboard, name='leaderboard'),
    path('profile/', views.profile, name='profile'),
    path('register/', views.register, name='register'),
    path('logout/', views.logout_view, name='logout'),



        # New URLs
    path('create-quest/', views.create_custom_quest, name='create_quest'),
    path('update-quest/<int:quest_id>/', views.update_quest_progress, name='update_quest'),
    path('notifications/', views.get_notifications, name='get_notifications'),
    path('mark-notification-read/<int:notification_id>/', views.mark_notification_read, name='mark_notification_read'),

]