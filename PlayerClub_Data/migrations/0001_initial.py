
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Club',
            fields=[
                ('id', models.IntegerField(primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=200, unique=True)),
                ('country', models.CharField(blank=True, max_length=100, null=True)),
                ('code', models.CharField(blank=True, max_length=50, null=True)),
                ('stadium', models.CharField(blank=True, max_length=200, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='Player',
            fields=[
                ('id', models.IntegerField(primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=200)),
                ('position', models.CharField(blank=True, max_length=50, null=True)),
                ('date_of_birth', models.DateField(blank=True, null=True)),
                ('height_cm', models.FloatField(blank=True, null=True)),
                ('total_goals', models.PositiveIntegerField(default=0)),
                ('total_assists', models.PositiveIntegerField(default=0)),
                ('yellow_cards', models.PositiveIntegerField(default=0)),
                ('red_cards', models.PositiveIntegerField(default=0)),
                ('total_win', models.PositiveIntegerField(default=0)),
                ('club', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='players', to='PlayerClub_Data.club')),
            ],
        ),
    ]
