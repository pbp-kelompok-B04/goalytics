from django import forms
from .models import Profile

class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ["preferred_league", "favorite_club", "display_mode", "bio"]
        widgets = {"bio": forms.Textarea(attrs={"rows": 4})}
