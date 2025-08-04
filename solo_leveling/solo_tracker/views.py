from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, authenticate,logout
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from django.db.models import Count, Sum
from .models import UserProfile, Quest, UserQuest, QuestCategory, Achievement, UserAchievement,Notification,CustomQuest
from .forms import QuestCompletionForm,CustomQuestForm
import json

def home(request):
    # if request.user.is_authenticated:
    #     return redirect('solo_tracker:home')
    return render(request, 'solo_tracker/home.html')


def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Create user profile
            UserProfile.objects.create(user=user)
            username = form.cleaned_data.get('username')
            messages.success(request, f'Account created for {username}!')
            return redirect('solo_tracker:login')
    else:
        form = UserCreationForm()
    return render(request, 'registration/register.html', {'form': form})


@login_required
def logout_view(request):
    logout(request)
    return redirect('solo_tracker:login') 
@login_required
def create_custom_quest(request):
    if request.method == 'POST':
        form = CustomQuestForm(request.POST)
        if form.is_valid():
            quest = form.save(commit=False)
            quest.user = request.user
            
            # Calculate XP reward based on difficulty and target count
            base_xp = {
                'Easy': 50,
                'Medium': 100,
                'Hard': 200,
                'Epic': 400
            }
            quest.xp_reward = base_xp[quest.difficulty] * quest.target_count
            quest.save()
            
            # Create notification
            Notification.objects.create(
                user=request.user,
                notification_type='quest_reminder',
                title='New Quest Created',
                message=f'Quest "{quest.title}" has been added to your list.',
                data={'quest_id': quest.id}
            )
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'message': 'Quest created successfully!',
                    'quest': {
                        'id': quest.id,
                        'title': quest.title,
                        'description': quest.description,
                        'difficulty': quest.difficulty,
                        'xp_reward': quest.xp_reward,
                        'progress_percentage': quest.progress_percentage
                    }
                })
            
            messages.success(request, 'Quest created successfully!')
            return redirect('solo_tracker:dashboard')
    else:
        form = CustomQuestForm()
    
    return render(request, 'solo_tracker/create_quest.html', {'form': form})

@login_required
def update_quest_progress(request, quest_id):
    if request.method == 'POST':
        quest = get_object_or_404(CustomQuest, id=quest_id, user=request.user)
        
        # Increment progress
        quest.current_count += 1
        
        # Check if quest is completed
        if quest.current_count >= quest.target_count and not quest.is_completed:
            quest.is_completed = True
            quest.completed_at = timezone.now()
            
            # Add XP to user
            profile = request.user.userprofile
            level_info = profile.add_xp(quest.xp_reward)
            
            # Create completion notification
            Notification.objects.create(
                user=request.user,
                notification_type='achievement',
                title='Quest Completed!',
                message=f'You completed "{quest.title}" and gained {quest.xp_reward} XP!',
                data={
                    'quest_id': quest.id,
                    'xp_gained': quest.xp_reward,
                    'level_up': level_info['level_up']
                }
            )
            
            # Check for level up notification
            if level_info['level_up']:
                old_job = UserProfile.objects.get(user=request.user).job_class
                profile.refresh_from_db()
                
                # Job change notification
                if old_job != profile.job_class:
                    Notification.objects.create(
                        user=request.user,
                        notification_type='job_change',
                        title='Job Changed!',
                        message=f'Your job has changed from {old_job} to {profile.job_class}',
                        data={
                            'old_job': old_job,
                            'new_job': profile.job_class,
                            'new_level': profile.level
                        }
                    )
                
                # Level up notification
                Notification.objects.create(
                    user=request.user,
                    notification_type='level_up',
                    title='Level Up!',
                    message=f'Congratulations! You reached Level {profile.level}!',
                    data={
                        'old_level': level_info['old_level'],
                        'new_level': level_info['new_level'],
                        'stats_gained': level_info['stats_gained']
                    }
                )
        
        quest.save()
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'completed': quest.is_completed,
                'progress': quest.progress_percentage,
                'current_count': quest.current_count,
                'target_count': quest.target_count
            })
        
        return redirect('solo_tracker:dashboard')

@login_required
def get_notifications(request):
    notifications = Notification.objects.filter(
        user=request.user,
        is_read=False
    )[:5]  # Get latest 5 unread notifications
    
    notification_data = []
    for notification in notifications:
        notification_data.append({
            'id': notification.id,
            'type': notification.notification_type,
            'title': notification.title,
            'message': notification.message,
            'data': notification.data,
            'created_at': notification.created_at.isoformat()
        })
    
    return JsonResponse({
        'notifications': notification_data,
        'count': len(notification_data)
    })

@login_required
def mark_notification_read(request, notification_id):
    if request.method == 'POST':
        notification = get_object_or_404(Notification, id=notification_id, user=request.user)
        notification.is_read = True
        notification.save()
        
        return JsonResponse({'success': True})
    
    return JsonResponse({'success': False})

@login_required
def dashboard(request):
    # Get or create user profile
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    
    # Update streak
    today = timezone.now().date()
    if profile.last_activity < today:
        # Check if user completed any quests yesterday
        yesterday = today - timezone.timedelta(days=1)
        completed_yesterday = UserQuest.objects.filter(
            user=request.user,
            completed=True,
            date_assigned=yesterday
        ).exists()
        
        if completed_yesterday and profile.last_activity == yesterday:
            profile.streak += 1
        elif profile.last_activity < yesterday:
            profile.streak = 0
        
        profile.last_activity = today
        profile.save()
    
    # Get today's quests
    today_quests = UserQuest.objects.filter(
        user=request.user,
        date_assigned=today
    ).select_related('quest', 'quest__category')
    
    # If no quests for today, create them
    if not today_quests.exists():
        daily_quests = Quest.objects.filter(is_daily=True, is_active=True)[:4]
        for quest in daily_quests:
            UserQuest.objects.create(
                user=request.user,
                quest=quest,
                date_assigned=today
            )
        today_quests = UserQuest.objects.filter(
            user=request.user,
            date_assigned=today
        ).select_related('quest', 'quest__category')
        # Get custom quests
    custom_quests = CustomQuest.objects.filter(
        user=request.user,
        is_completed=False
    ).order_by('-created_at')
    
    # Get leaderboard
    leaderboard = UserProfile.objects.select_related('user').order_by('-total_xp')[:10]
    
    # Get weekly progress
    week_start = today - timezone.timedelta(days=today.weekday())
    weekly_stats = UserQuest.objects.filter(
        user=request.user,
        completed=True,
        date_assigned__gte=week_start
    ).values('quest__category__name').annotate(
        count=Count('id')
    )
    
    # Calculate weekly progress percentages
    weekly_progress = {}
    for stat in weekly_stats:
        category = stat['quest__category__name']
        count = stat['count']
        # Assuming 7 quests per week per category as target
        percentage = min((count / 7) * 100, 100)
        weekly_progress[category] = percentage

        # Get recent notifications
    notifications = Notification.objects.filter(
        user=request.user,
        is_read=False
    )[:3]
    
    context = {
        'profile': profile,
        'today_quests': today_quests,
        'custom_quests': custom_quests,
        'notifications': notifications,
        'leaderboard': leaderboard,
        'weekly_progress': weekly_progress,
        'completed_quests_count': UserQuest.objects.filter(user=request.user, completed=True).count(),
    }
    
    return render(request, 'solo_tracker/dashboard.html', context)

@login_required
def complete_quest(request, quest_id):
    if request.method == 'POST':
        user_quest = get_object_or_404(
            UserQuest, 
            id=quest_id, 
            user=request.user, 
            completed=False
        )
        
        # Mark quest as completed
        user_quest.completed = True
        user_quest.completed_at = timezone.now()
        user_quest.save()
        
        # Add XP to user
        profile = request.user.userprofile
        old_level = profile.level
        new_level = profile.add_xp(user_quest.quest.xp_reward)
        
        # Check for level up
        level_up = new_level > old_level
        
        # Check for achievements
        check_achievements(request.user)
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'level_up': level_up,
                'new_level': new_level,
                'xp_gained': user_quest.quest.xp_reward,
                'current_xp': profile.current_xp,
                'total_xp': profile.total_xp,
            })
        
        if level_up:
            messages.success(request, f'Quest completed! Level up! You are now level {new_level}!')
        else:
            messages.success(request, f'Quest completed! +{user_quest.quest.xp_reward} XP')
        
        return redirect('solo_tracker:dashboard')
    
    return redirect('solo_tracker:dashboard')

def check_achievements(user):
    profile = user.userprofile
    achievements = Achievement.objects.all()
    
    for achievement in achievements:
        # Skip if user already has this achievement
        if UserAchievement.objects.filter(user=user, achievement=achievement).exists():
            continue
        
        earned = False
        
        if achievement.requirement_type == 'level':
            earned = profile.level >= achievement.requirement_value
        elif achievement.requirement_type == 'streak':
            earned = profile.streak >= achievement.requirement_value
        elif achievement.requirement_type == 'quests_completed':
            completed_count = UserQuest.objects.filter(user=user, completed=True).count()
            earned = completed_count >= achievement.requirement_value
        
        if earned:
            UserAchievement.objects.create(user=user, achievement=achievement)
            if achievement.xp_reward > 0:
                profile.add_xp(achievement.xp_reward)

@login_required
def leaderboard(request):
    leaderboard = UserProfile.objects.select_related('user').order_by('-total_xp')[:50]
    context = {
        'leaderboard': leaderboard,
        'user_profile': request.user.userprofile,
    }
    return render(request, 'solo_tracker/leaderboard.html', context)

@login_required
def profile(request):
    profile = request.user.userprofile
    achievements = UserAchievement.objects.filter(user=request.user).select_related('achievement')
    
    # Get quest completion stats
    total_quests = UserQuest.objects.filter(user=request.user).count()
    completed_quests = UserQuest.objects.filter(user=request.user, completed=True).count()
    completion_rate = (completed_quests / total_quests * 100) if total_quests > 0 else 0
    
    # Get category stats
    category_stats = UserQuest.objects.filter(
        user=request.user, 
        completed=True
    ).values(
        'quest__category__name'
    ).annotate(
        count=Count('id')
    ).order_by('-count')
    
    context = {
        'profile': profile,
        'achievements': achievements,
        'total_quests': total_quests,
        'completed_quests': completed_quests,
        'completion_rate': completion_rate,
        'category_stats': category_stats,
    }
    
    return render(request, 'solo_tracker/profile.html', context)
