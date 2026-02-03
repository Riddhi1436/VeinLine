from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0002_seed_compatibility'),
    ]

    operations = [
        migrations.CreateModel(
            name='BloodBank',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
                ('city', models.CharField(max_length=64)),
                ('address', models.CharField(max_length=500)),
                ('phone', models.CharField(blank=True, max_length=20)),
                ('email', models.EmailField(blank=True, max_length=254)),
                ('latitude', models.DecimalField(decimal_places=6, max_digits=9)),
                ('longitude', models.DecimalField(decimal_places=6, max_digits=9)),
                ('opening_time', models.TimeField(default='08:00')),
                ('closing_time', models.TimeField(default='18:00')),
                ('description', models.TextField(blank=True)),
                ('website', models.URLField(blank=True)),
                ('is_active', models.BooleanField(default=True)),
                ('accepts_walk_in', models.BooleanField(default=True)),
                ('has_emergency_service', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'ordering': ['city', 'name'],
            },
        ),
        migrations.AddIndex(
            model_name='bloodbank',
            index=models.Index(fields=['city', 'is_active'], name='core_bloodbank_city_is_active_idx'),
        ),
        migrations.AddIndex(
            model_name='bloodbank',
            index=models.Index(fields=['latitude', 'longitude'], name='core_bloodbank_latitude_longitude_idx'),
        ),
    ]
