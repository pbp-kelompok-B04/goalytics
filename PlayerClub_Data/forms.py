from django import forms
from .models import Player, Club

class PlayerForm(forms.ModelForm):
    class Meta:
        model = Player
        fields = [
            'name', 'club', 'position', 'date_of_birth', 
            'height_cm', 'total_goals', 'total_assists', 
            'yellow_cards', 'red_cards', 'total_win'
        ]
        widgets = {
            'date_of_birth': forms.DateInput(attrs={'type': 'date', 'class': 'form-input'}),
            'name': forms.TextInput(attrs={'class': 'form-input'}),
            'position': forms.TextInput(attrs={'class': 'form-input'}),
            'club': forms.Select(attrs={'class': 'form-select'}),
        }

class ClubForm(forms.ModelForm):
    class Meta:
        model = Club
        fields = ['name', 'country', 'code', 'stadium']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-input'}),
            'country': forms.TextInput(attrs={'class': 'form-input'}),
            'code': forms.TextInput(attrs={'class': 'form-input'}),
            'stadium': forms.TextInput(attrs={'class': 'form-input'}),
        }
