from django.db import models
from django.contrib.auth.models import User

# Create your models here.
LEAGUE_CHOICES = (
    ("EPL", "Premier League"),
    ("LALIGA", "La Liga"),
    ("SERIEA", "Serie A"),
    ("BUNDES", "Bundesliga"),
    ("LIGUE1", "Ligue 1"),
)

class Post(models.Model):
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='posts')
    title = models.CharField(max_length=200)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    likes = models.ManyToManyField(User, related_name='liked_post')
    league = models.CharField(max_length=20, choices=LEAGUE_CHOICES, default="EPL")

    def __str__(self):
        return self.title
    
class Comment(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='comments')
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    parent = models.ForeignKey('self',null=True,blank=True,on_delete=models.CASCADE,related_name='replies')
    likes = models.ManyToManyField(User, related_name='liked_comment')

    @property
    def is_parent(self):
        return self.parent is None
    
class Notification(models.Model):
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name="notifications")
    actor = models.ForeignKey(User, on_delete=models.CASCADE, related_name="sent_notifications")
    verb = models.CharField(max_length=255)  # contoh: "liked your post", "commented on your comment"
    target_post = models.ForeignKey(Post, on_delete=models.CASCADE, null=True, blank=True)
    target_comment = models.ForeignKey(Comment, on_delete=models.CASCADE, null=True, blank=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.actor.username} {self.verb}"

