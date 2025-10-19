from django import forms
from .models import Profile
from PlayerClub_Data.models import Club

base_input = {'class': 'w-full p-2 border rounded-lg'}

class ProfileForm(forms.ModelForm):
    favorite_team = forms.ModelChoiceField(
        queryset=Club.objects.order_by('name'),
        required=False,
        empty_label="— Select favorite club —",
        widget=forms.Select(attrs=base_input),
        label="Favorite Club",
    )

    class Meta:
        model = Profile
        fields = ['profile_picture', 'bio', 'favorite_team', 'instagram_url', 'x_url', 'website_url']
        widgets = {
            'bio': forms.Textarea(attrs={**base_input, 'rows': 3}),
            'profile_picture': forms.URLInput(attrs=base_input),
            'instagram_url': forms.URLInput(attrs=base_input),
            'x_url': forms.URLInput(attrs=base_input),
            'website_url': forms.URLInput(attrs=base_input),
        }
