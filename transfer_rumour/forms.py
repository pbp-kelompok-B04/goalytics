from django import forms

from .models import TransferRumour


class TransferRumourForm(forms.ModelForm):
    class Meta:
        model = TransferRumour
        fields = ["title", "summary", "cover_image_url", "content", "source_url"]
        widgets = {
            "title": forms.TextInput(attrs={"class": "w-full rounded-lg border px-3 py-2"}),
            "summary": forms.Textarea(
                attrs={
                    "class": "w-full rounded-lg border px-3 py-2",
                    "rows": 2,
                    "placeholder": "Ringkasan singkat (opsional)",
                }
            ),
            "cover_image_url": forms.URLInput(
                attrs={
                    "class": "w-full rounded-lg border px-3 py-2",
                    "placeholder": "Tautan gambar sampul (opsional)",
                }
            ),
            "content": forms.Textarea(
                attrs={
                    "class": "w-full rounded-lg border px-3 py-2",
                    "rows": 8,
                    "placeholder": "Detail rumour transfer...",
                }
            ),
            "source_url": forms.URLInput(
                attrs={
                    "class": "w-full rounded-lg border px-3 py-2",
                    "placeholder": "Tautan sumber (opsional)",
                }
            ),
        }
