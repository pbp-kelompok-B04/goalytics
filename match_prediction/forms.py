from django import forms
from .models import Match, Prediction
from django.utils.html import format_html


class MatchForm(forms.ModelForm):
    """
    Used by admins/analysts to create or edit a match (forum).
    """
    class Meta:
        model = Match
        fields = ['home_club', 'away_club', 'match_datetime', 'venue', 'is_active']
        widgets = {
            'match_datetime': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'venue': forms.TextInput(attrs={'placeholder': 'Enter venue name...'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Defensive: if the PlayerClub_Data app is present, set an ordered queryset
        try:
            from PlayerClub_Data.models import Club
            qs = Club.objects.all().order_by('name')    # deterministic ordering
            # set the queryset for both selectors
            self.fields['home_club'].queryset = qs
            self.fields['away_club'].queryset = qs


        except Exception:
            pass

    def clean(self):
        cleaned_data = super().clean()
        home = cleaned_data.get('home_club')
        away = cleaned_data.get('away_club')
        if home and away and home == away:
            raise forms.ValidationError("Home and Away clubs cannot be the same.")
        return cleaned_data


class PredictionForm(forms.ModelForm):
    """
    Used by users to create or edit their predictions.
    """
    class Meta:
        model = Prediction
        fields = ['predicted_home_score', 'predicted_away_score', 'explanation']
        widgets = {
            'predicted_home_score': forms.NumberInput(attrs={'min': 0}),
            'predicted_away_score': forms.NumberInput(attrs={'min': 0}),
            'explanation': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Explain your reasoning (optional)...'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        home_score = cleaned_data.get('predicted_home_score')
        away_score = cleaned_data.get('predicted_away_score')

        if home_score is None or away_score is None:
            raise forms.ValidationError("Please fill in both predicted scores.")
        if home_score < 0 or away_score < 0:
            raise forms.ValidationError("Scores cannot be negative.")
        return cleaned_data