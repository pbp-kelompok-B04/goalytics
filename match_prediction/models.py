from django.db import models
from django.conf import settings
from django.utils import timezone
from django.core.exceptions import ValidationError

User = settings.AUTH_USER_MODEL  # uses django.contrib.auth.models.User as requested


class Match(models.Model):
    """
    The forum card created by admin/analyst.
    Title can be auto-generated with `title` property (Team A vs Team B).
    """
    # NOTE: you requested this exact FK signature; I'm including it explicitly as an optional field
    # for integration with your PlayerClub_Data app. If you'd rather only have home/away, you can remove this.

    home_club = models.ForeignKey('PlayerClub_Data.Club', on_delete=models.SET_NULL, null=True, blank=True, related_name='home_matches')
    away_club = models.ForeignKey('PlayerClub_Data.Club', on_delete=models.SET_NULL, null=True, blank=True, related_name='away_matches')

    match_datetime = models.DateTimeField(null=True, blank=True)
    venue = models.CharField(max_length=255, blank=True)

    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_matches')
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    is_active = models.BooleanField(default=True)  # admins/analysts can deactivate/delete

    class Meta:
        ordering = ['-match_datetime', '-created_at']
        indexes = [
            models.Index(fields=['match_datetime']),
        ]

    def __str__(self):
        return self.title

    @property
    def title(self):
        """Return 'Team A vs Team B' — fallback to placeholder when clubs missing."""
        a = self.home_club.name if self.home_club else "TBD"
        b = self.away_club.name if self.away_club else "TBD"
        return f"{a} vs {b}"
    
    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('match_prediction:match_detail', args=[str(self.id)])
    
    def clean(self):
        if self.home_club and self.away_club and self.home_club == self.away_club:
            raise ValidationError("Home and Away clubs cannot be the same.")

    def save(self, *args, **kwargs):
        self.clean()  # ensure validation always enforced
        super().save(*args, **kwargs)


class Prediction(models.Model):
    """
    A user's prediction (one prediction is a forum post inside a Match).
    Users may post multiple predictions per match (allowed). If you want to restrict
    one active prediction per user per match, we can add a UniqueConstraint later.
    """
    match = models.ForeignKey(Match, on_delete=models.CASCADE, related_name='predictions')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='predictions')

    # structured prediction fields (scores)
    predicted_home_score = models.PositiveSmallIntegerField(null=True, blank=True)
    predicted_away_score = models.PositiveSmallIntegerField(null=True, blank=True)

    # optional textual explanation (forum post body)
    explanation = models.TextField(blank=True)

    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    

    # soft delete flag (optional; admin can hard-delete if needed)
    is_deleted = models.BooleanField(default=False)

    # upvotes will be tracked via PredictionUpvote (see below)
    upvote_count = models.PositiveIntegerField(default=0, editable=False)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['match', 'user']),
        ]
        constraints = [
            # This constraint now ONLY applies to predictions where is_deleted=False
            models.UniqueConstraint(
                fields=['user', 'match'], 
                condition=models.Q(is_deleted=False), # ⬅️ CRITICAL FIX
                name='unique_active_user_prediction_per_match'
            )
        ]

    def __str__(self):
        return f"Prediction by {self.user} for {self.match.title}"

    def recalc_upvote_count(self):
        """Call to re-sync upvote_count with actual upvotes (safe to run periodically)."""
        self.upvote_count = self.upvotes.count()
        self.save(update_fields=['upvote_count'])


class PredictionUpvote(models.Model):
    """
    Through model to record which user upvoted which prediction and when.
    Ensures one upvote per user per prediction with a DB-level unique constraint.
    """
    prediction = models.ForeignKey(Prediction, on_delete=models.CASCADE, related_name='upvote_links')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='prediction_upvotes')
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = ('prediction', 'user')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user} upvoted {self.prediction_id}"


# To make upvoting easy to use from Prediction, add a M2M via property:
Prediction.add_to_class(
    'upvotes',
    models.ManyToManyField(User, through=PredictionUpvote, related_name='upvoted_predictions', blank=True)
)