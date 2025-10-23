from django import forms
from .models import FavoritePlayer

class FavoritePlayerForm(forms.ModelForm):
    class Meta:
        model = FavoritePlayer
        fields = ['player']
