from django.conf import settings
from django.db import models
from django.urls import reverse
from django.utils.text import slugify


class TransferRumour(models.Model):
    """Represents a transfer rumour article created by privileged users."""

    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True, blank=True)
    summary = models.CharField(max_length=280, blank=True)
    content = models.TextField()
    source_url = models.URLField(blank=True)
    cover_image_url = models.URLField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="transfer_rumours",
    )

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.title)[:200] or "transfer-rumour"
            slug = base_slug
            suffix = 1
            while TransferRumour.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                suffix += 1
                slug = f"{base_slug}-{suffix}"
            self.slug = slug
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("transfer_rumour:detail", kwargs={"slug": self.slug})
