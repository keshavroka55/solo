from django.contrib import admin
from .models import *

# Register your models here.

admin.site.register(UserProfile)
admin.site.register(QuestCategory)
admin.site.register(Quest)
admin.site.register(UserQuest)
admin.site.register(Achievement)
admin.site.register(UserAchievement)
admin.site.register(CustomQuest)
admin.site.register(Notification)



