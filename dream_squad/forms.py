# forms.py
from django import forms
from .models import DreamSquad

class DreamSquadForm(forms.ModelForm):
    class Meta:
        model = DreamSquad
        fields = ['name']
        widgets = {
            'name': forms.TextInput(attrs={'placeholder': 'My Dream Squad'}),
        }
