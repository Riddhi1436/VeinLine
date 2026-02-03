from django.db import migrations, models
import django.db.models.deletion
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('donations', '0002_donor_statistics'),
        ('sos', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='DonorFeedback',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('rating', models.PositiveSmallIntegerField(choices=[(5, '⭐⭐⭐⭐⭐ Excellent'), (4, '⭐⭐⭐⭐ Good'), (3, '⭐⭐⭐ Average'), (2, '⭐⭐ Poor'), (1, '⭐ Very Poor')], default=5)),
                ('message', models.TextField(help_text='Thank you message or feedback')),
                ('is_public', models.BooleanField(default=True, help_text="Show on donor's public profile")),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('donor', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='received_feedback', to=settings.AUTH_USER_MODEL)),
                ('patient', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='given_feedback', to=settings.AUTH_USER_MODEL)),
                ('sos_request', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='sos.sosrequest')),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
        migrations.AddIndex(
            model_name='donorfeedback',
            index=models.Index(fields=['donor', '-created_at'], name='donations_donorfeedback_donor_created_idx'),
        ),
    ]
