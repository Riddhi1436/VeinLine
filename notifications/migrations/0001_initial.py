from django.db import migrations, models
import django.db.models.deletion
from django.conf import settings


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Notification',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('notification_type', models.CharField(choices=[('sos_request', 'New SOS Request'), ('sos_response', 'SOS Response Received'), ('sos_fulfilled', 'SOS Request Fulfilled'), ('appointment_reminder', 'Appointment Reminder'), ('appointment_confirmed', 'Appointment Confirmed'), ('appointment_cancelled', 'Appointment Cancelled'), ('new_badge', 'Achievement Badge Earned'), ('donor_thank_you', 'Donor Thank You Message'), ('activity', 'Activity Update'), ('system', 'System Message')], max_length=32)),
                ('title', models.CharField(max_length=255)),
                ('message', models.TextField()),
                ('is_read', models.BooleanField(default=False)),
                ('read_at', models.DateTimeField(blank=True, null=True)),
                ('channels', models.JSONField(default=list, help_text='List of channels: in_app, email, sms, push')),
                ('priority', models.CharField(choices=[('low', 'Low'), ('normal', 'Normal'), ('high', 'High'), ('urgent', 'Urgent')], default='normal', max_length=16)),
                ('action_url', models.CharField(blank=True, help_text='URL to navigate to when clicked', max_length=255)),
                ('icon', models.CharField(blank=True, help_text='Emoji or icon to display', max_length=64)),
                ('object_id', models.PositiveIntegerField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('content_type', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='contenttypes.contenttype')),
                ('recipient', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='notifications', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='NotificationPreference',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('enable_in_app', models.BooleanField(default=True)),
                ('enable_email', models.BooleanField(default=True)),
                ('enable_sms', models.BooleanField(default=True)),
                ('enable_push', models.BooleanField(default=False)),
                ('notify_sos_requests', models.BooleanField(default=True)),
                ('notify_sos_responses', models.BooleanField(default=True)),
                ('notify_appointments', models.BooleanField(default=True)),
                ('notify_achievements', models.BooleanField(default=True)),
                ('notify_thank_you_messages', models.BooleanField(default=True)),
                ('notify_system_messages', models.BooleanField(default=True)),
                ('quiet_hours_start', models.TimeField(blank=True, help_text='e.g., 22:00', null=True)),
                ('quiet_hours_end', models.TimeField(blank=True, help_text='e.g., 08:00', null=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='notification_preferences', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.AddIndex(
            model_name='notification',
            index=models.Index(fields=['recipient', '-created_at'], name='notifications_notification_recipient_created_idx'),
        ),
        migrations.AddIndex(
            model_name='notification',
            index=models.Index(fields=['recipient', 'is_read'], name='notifications_notification_recipient_is_read_idx'),
        ),
        migrations.AddIndex(
            model_name='notification',
            index=models.Index(fields=['-created_at'], name='notifications_notification_created_idx'),
        ),
    ]
