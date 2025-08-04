from .models import UserQuest,CustomQuest
from django import forms


class QuestCompletionForm(forms.Form):
    quest_id = forms.IntegerField(widget=forms.HiddenInput())


class CustomQuestForm(forms.ModelForm):
    class Meta:
        model = CustomQuest
        fields = ['title', 'description', 'difficulty', 'quest_type', 'target_count', 'reminder_time', 'reminder_enabled']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'w-full bg-transparent border-b-2 border-cyan-400/50 focus:border-cyan-400 text-white placeholder-gray-400 py-3 px-0 transition-all duration-300 focus:outline-none',
                'placeholder': 'Enter quest title'
            }),
            'description': forms.Textarea(attrs={
                'class': 'w-full bg-slate-800/50 border border-cyan-400/30 rounded-lg text-white placeholder-gray-400 p-4 focus:outline-none focus:border-cyan-400 transition-all duration-300',
                'placeholder': 'Describe your quest...',
                'rows': 4
            }),
            'difficulty': forms.Select(attrs={
                'class': 'w-full bg-slate-800/50 border border-cyan-400/30 rounded-lg text-white p-3 focus:outline-none focus:border-cyan-400 transition-all duration-300'
            }),
            'quest_type': forms.Select(attrs={
                'class': 'w-full bg-slate-800/50 border border-cyan-400/30 rounded-lg text-white p-3 focus:outline-none focus:border-cyan-400 transition-all duration-300'
            }),
            'target_count': forms.NumberInput(attrs={
                'class': 'w-full bg-transparent border-b-2 border-cyan-400/50 focus:border-cyan-400 text-white placeholder-gray-400 py-3 px-0 transition-all duration-300 focus:outline-none',
                'placeholder': '1',
                'min': '1'
            }),
            'reminder_time': forms.TimeInput(attrs={
                'class': 'w-full bg-slate-800/50 border border-cyan-400/30 rounded-lg text-white p-3 focus:outline-none focus:border-cyan-400 transition-all duration-300',
                'type': 'time'
            }),
            'reminder_enabled': forms.CheckboxInput(attrs={
                'class': 'rounded bg-transparent border-cyan-400/50 text-cyan-400 focus:ring-cyan-400 focus:ring-offset-0'
            })
        }
