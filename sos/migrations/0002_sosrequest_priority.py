from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('sos', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='sosrequest',
            name='priority',
            field=models.CharField(choices=[('normal', 'Normal'), ('urgent', 'Urgent (24 hours)'), ('critical', 'Critical (Immediate)')], default='normal', max_length=16),
        ),
        migrations.AddIndex(
            model_name='sosrequest',
            index=models.Index(fields=['priority', 'status'], name='sos_sosrequest_priority_status_idx'),
        ),
    ]
