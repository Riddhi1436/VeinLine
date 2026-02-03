from django.db import migrations, models
import django.db.models.deletion
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('donations', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='DonorStatistics',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('total_donations', models.PositiveIntegerField(default=0)),
                ('total_lives_saved', models.PositiveIntegerField(default=0)),
                ('sos_responses', models.PositiveIntegerField(default=0)),
                ('successful_sos_responses', models.PositiveIntegerField(default=0)),
                ('badges', models.JSONField(default=list, help_text='List of badge types earned')),
                ('rank', models.PositiveIntegerField(default=0, help_text='Leaderboard rank')),
                ('points', models.PositiveIntegerField(default=0, help_text='Accumulated points for achievements')),
                ('current_donation_streak', models.PositiveIntegerField(default=0, help_text='Months of consecutive donations')),
                ('last_donation_streak_date', models.DateField(blank=True, null=True)),
                ('response_rate', models.FloatField(default=0.0, help_text='SOS response acceptance rate (0-100)')),
                ('average_response_time_hours', models.FloatField(default=0.0, help_text='Average hours to respond to SOS')),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('donor', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='donor_stats', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name_plural': 'Donor Statistics',
            },
        ),
    ]
