from django import forms
from .models import Player, Club


class PlayerForm(forms.ModelForm):
    # Limit position to model's 4 choices
    position = forms.ChoiceField(
        choices=Player.POSITION_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    class Meta:
        model = Player
        fields = [
            'name', 'nation', 'position', 'age', 'born', 'club',
            'goals', 'assists', 'xg', 'npxg', 'xag',
            'Progressive_Carries', 'Progressive_Passes', 'Progressive_Receptions',
            'passes_completed', 'passes_attempted', 'pass_accuracy',
            'tackles', 'tackles_won', 'challenges_won', 'challenges_attempted',
            'blocks', 'clearances',
            'saves', 'save_percentage', 'clean_sheets', 'clean_sheet_percentage',
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-input'}),
            'nation': forms.TextInput(attrs={'class': 'form-input'}),
            'age': forms.NumberInput(attrs={'class': 'form-input', 'min': 0, 'step': 1}),
            'born': forms.NumberInput(attrs={'class': 'form-input', 'min': 0, 'step': 1}),
            'club': forms.Select(attrs={'class': 'form-select'}),

            'goals': forms.NumberInput(attrs={'class': 'form-input', 'step': 0.01}),
            'assists': forms.NumberInput(attrs={'class': 'form-input', 'step': 0.01}),
            'xg': forms.NumberInput(attrs={'class': 'form-input', 'step': 0.01}),
            'npxg': forms.NumberInput(attrs={'class': 'form-input', 'step': 0.01}),
            'xag': forms.NumberInput(attrs={'class': 'form-input', 'step': 0.01}),

            'Progressive_Carries': forms.NumberInput(attrs={'class': 'form-input', 'step': 0.01}),
            'Progressive_Passes': forms.NumberInput(attrs={'class': 'form-input', 'step': 0.01}),
            'Progressive_Receptions': forms.NumberInput(attrs={'class': 'form-input', 'step': 0.01}),

            'passes_completed': forms.NumberInput(attrs={'class': 'form-input', 'step': 1, 'min': 0}),
            'passes_attempted': forms.NumberInput(attrs={'class': 'form-input', 'step': 1, 'min': 0}),
            'pass_accuracy': forms.NumberInput(attrs={'class': 'form-input', 'step': 0.01, 'min': 0}),

            'tackles': forms.NumberInput(attrs={'class': 'form-input', 'step': 1, 'min': 0}),
            'tackles_won': forms.NumberInput(attrs={'class': 'form-input', 'step': 1, 'min': 0}),
            'challenges_won': forms.NumberInput(attrs={'class': 'form-input', 'step': 1, 'min': 0}),
            'challenges_attempted': forms.NumberInput(attrs={'class': 'form-input', 'step': 1, 'min': 0}),
            'blocks': forms.NumberInput(attrs={'class': 'form-input', 'step': 1, 'min': 0}),
            'clearances': forms.NumberInput(attrs={'class': 'form-input', 'step': 1, 'min': 0}),

            'saves': forms.NumberInput(attrs={'class': 'form-input', 'step': 1, 'min': 0}),
            'save_percentage': forms.NumberInput(attrs={'class': 'form-input', 'step': 0.01, 'min': 0}),
            'clean_sheets': forms.NumberInput(attrs={'class': 'form-input', 'step': 1, 'min': 0}),
            'clean_sheet_percentage': forms.NumberInput(attrs={'class': 'form-input', 'step': 0.01, 'min': 0}),
        }


class ClubForm(forms.ModelForm):
    class Meta:
        model = Club
        fields = [
            'league', 'season', 'name',
            'total_goal', 'total_assist', 'expected_xg', 'expected_xag',
        ]
        widgets = {
            'league': forms.TextInput(attrs={'class': 'form-input'}),
            'season': forms.TextInput(attrs={'class': 'form-input'}),
            'name': forms.TextInput(attrs={'class': 'form-input'}),
            'total_goal': forms.NumberInput(attrs={'class': 'form-input', 'step': 1, 'min': 0}),
            'total_assist': forms.NumberInput(attrs={'class': 'form-input', 'step': 1, 'min': 0}),
            'expected_xg': forms.NumberInput(attrs={'class': 'form-input', 'step': 0.01}),
            'expected_xag': forms.NumberInput(attrs={'class': 'form-input', 'step': 0.01}),
        }
