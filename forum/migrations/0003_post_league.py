from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('forum', '0002_comment_likes_post_likes'),
    ]

    operations = [
        migrations.AddField(
            model_name='post',
            name='league',
            field=models.CharField(
                choices=[
                    ('EPL', 'Premier League'),
                    ('LALIGA', 'La Liga'),
                    ('SERIEA', 'Serie A'),
                    ('BUNDES', 'Bundesliga'),
                    ('LIGUE1', 'Ligue 1'),
                ],
                default='EPL',
                max_length=20,
            ),
        ),
    ]

