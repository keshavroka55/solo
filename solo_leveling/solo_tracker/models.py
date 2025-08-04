from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    level = models.IntegerField(default=1)
    current_xp = models.IntegerField(default=0)
    total_xp = models.IntegerField(default=0)
    streak = models.IntegerField(default=0)
    last_activity = models.DateField(default=timezone.now)
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)

        # New stats fields based on Solo Leveling
    strength = models.IntegerField(default=10)
    vitality = models.IntegerField(default=10)
    agility = models.IntegerField(default=10)
    intelligence = models.IntegerField(default=10)
    perception = models.IntegerField(default=10)
    
    # Job/Class system
    job_class = models.CharField(max_length=50, default='Hunter')
    job_title = models.CharField(max_length=100, default='E-Rank Hunter')
    
    def __str__(self):
        return f"{self.user.username} - Level {self.level}"
    
    @property
    def xp_to_next_level(self):
        return (self.level * 1000) - self.current_xp
    
    @property
    def xp_percentage(self):
        return (self.current_xp / (self.level * 1000)) * 100
    
    @property
    def rank(self):
        return UserProfile.objects.filter(total_xp__gt=self.total_xp).count() + 1
    
    def add_xp(self, amount):
        old_level = self.level
        self.current_xp += amount
        self.total_xp += amount
        
        # Check for level up
        while self.current_xp >= (self.level * 1000):
            self.current_xp -= (self.level * 1000)
            self.level += 1

                        # Increase stats on level up
            self.strength += 2
            self.vitality += 2
            self.agility += 2
            self.intelligence += 2
            self.perception += 2
            
            # Update job class based on level
            self.update_job_class()
        
        self.save()
        return {
            'level_up': self.level > old_level,
            'old_level': old_level,
            'new_level': self.level,
            'stats_gained': (self.level - old_level) * 2 if self.level > old_level else 0
        }
    
    def update_job_class(self):
        """Update job class based on level"""
        if self.level >= 100:
            self.job_class = 'Shadow Monarch'
            self.job_title = 'The One Who Overcame Adversity'
        elif self.level >= 80:
            self.job_class = 'Necromancer'
            self.job_title = 'Master of Death'
        elif self.level >= 60:
            self.job_class = 'Shadow Hunter'
            self.job_title = 'Elite Hunter'
        elif self.level >= 40:
            self.job_class = 'A-Rank Hunter'
            self.job_title = 'Advanced Hunter'
        elif self.level >= 20:
            self.job_class = 'B-Rank Hunter'
            self.job_title = 'Skilled Hunter'
        elif self.level >= 10:
            self.job_class = 'C-Rank Hunter'
            self.job_title = 'Intermediate Hunter'
        else:
            self.job_class = 'E-Rank Hunter'
            self.job_title = 'Novice Hunter'

class QuestCategory(models.Model):
    name = models.CharField(max_length=50)
    icon = models.CharField(max_length=50, default='target')
    color = models.CharField(max_length=20, default='blue')
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name_plural = "Quest Categories"

class Quest(models.Model):
    DIFFICULTY_CHOICES = [
        ('Easy', 'Easy'),
        ('Medium', 'Medium'),
        ('Hard', 'Hard'),
        ('Epic', 'Epic'),
    ]
    
    title = models.CharField(max_length=200)
    description = models.TextField()
    category = models.ForeignKey(QuestCategory, on_delete=models.CASCADE)
    difficulty = models.CharField(max_length=10, choices=DIFFICULTY_CHOICES)
    xp_reward = models.IntegerField()
    is_daily = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.title
    
    @property
    def difficulty_color(self):
        colors = {
            'Easy': 'green',
            'Medium': 'yellow',
            'Hard': 'red',
            'Epic': 'purple'
        }
        return colors.get(self.difficulty, 'gray')

class UserQuest(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    quest = models.ForeignKey(Quest, on_delete=models.CASCADE)
    completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)
    date_assigned = models.DateField(default=timezone.now)
    
    class Meta:
        unique_together = ['user', 'quest', 'date_assigned']
    
    def __str__(self):
        return f"{self.user.username} - {self.quest.title}"

class Achievement(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    icon = models.CharField(max_length=50, default='trophy')
    requirement_type = models.CharField(max_length=50)  # 'level', 'streak', 'quests_completed'
    requirement_value = models.IntegerField()
    xp_reward = models.IntegerField(default=0)
    
    def __str__(self):
        return self.name

class UserAchievement(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    achievement = models.ForeignKey(Achievement, on_delete=models.CASCADE)
    earned_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['user', 'achievement']
    
    def __str__(self):
        return f"{self.user.username} - {self.achievement.name}"
    

class Notification(models.Model):
    NOTIFICATION_TYPES = [
        ('level_up', 'Level Up'),
        ('job_change', 'Job Change'),
        ('quest_reminder', 'Quest Reminder'),
        ('achievement', 'Achievement'),
        ('warning', 'Warning'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)
    title = models.CharField(max_length=100)
    message = models.TextField()
    data = models.JSONField(default=dict, blank=True)  # Store additional data
    
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.title}"
    

class CustomQuest(models.Model):
    DIFFICULTY_CHOICES = [
        ('Easy', 'Easy'),
        ('Medium', 'Medium'),
        ('Hard', 'Hard'),
        ('Epic', 'Epic'),
    ]
    
    QUEST_TYPE_CHOICES = [
        ('daily', 'Daily Quest'),
        ('weekly', 'Weekly Quest'),
        ('custom', 'Custom Quest'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    description = models.TextField()
    difficulty = models.CharField(max_length=10, choices=DIFFICULTY_CHOICES)
    xp_reward = models.IntegerField()
    quest_type = models.CharField(max_length=10, choices=QUEST_TYPE_CHOICES, default='custom')
    
    # Timer-based notifications
    reminder_time = models.TimeField(null=True, blank=True)
    reminder_enabled = models.BooleanField(default=False)
    
    # Progress tracking
    target_count = models.IntegerField(default=1)
    current_count = models.IntegerField(default=0)
    
    is_completed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return f"{self.user.username} - {self.title}"
    
    @property
    def progress_percentage(self):
        return (self.current_count / self.target_count) * 100 if self.target_count > 0 else 0
    
    @property
    def is_overdue(self):
        if self.quest_type == 'daily':
            return timezone.now().date() > self.created_at.date()
        return False

