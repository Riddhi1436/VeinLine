from django.db import migrations, models
import django.db.models.deletion
import django.core.validators
from django.conf import settings
import datetime


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='AppointmentSlot',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('blood_bank', models.CharField(choices=[('red_crescent', 'Red Crescent Blood Bank'), ('city_hospital', 'City Hospital Blood Bank'), ('private_clinic', 'Private Clinic Blood Bank'), ('mobile_unit', 'Mobile Donation Unit')], max_length=50)),
                ('city', models.CharField(max_length=64)),
                ('address', models.CharField(blank=True, max_length=255)),
                ('date', models.DateField(validators=[django.core.validators.MinValueValidator(datetime.date.today())])),
                ('start_time', models.TimeField()),
                ('end_time', models.TimeField()),
                ('max_donors', models.PositiveIntegerField(default=10)),
                ('booked_donors', models.PositiveIntegerField(default=0)),
                ('status', models.CharField(choices=[('available', 'Available'), ('booked', 'Booked'), ('completed', 'Completed'), ('cancelled', 'Cancelled')], default='available', max_length=16)),
                ('notes', models.TextField(blank=True, help_text='Special instructions or requirements')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'ordering': ['-date', '-start_time'],
            },
        ),
        migrations.CreateModel(
            name='Appointment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('status', models.CharField(choices=[('scheduled', 'Scheduled'), ('confirmed', 'Confirmed'), ('completed', 'Completed'), ('no_show', 'No Show'), ('cancelled', 'Cancelled')], default='scheduled', max_length=16)),
                ('has_answered_health_questions', models.BooleanField(default=False)),
                ('health_check_passed', models.BooleanField(default=False)),
                ('is_confirmed_by_donor', models.BooleanField(default=False)),
                ('confirmed_at', models.DateTimeField(blank=True, null=True)),
                ('donation_completed', models.BooleanField(default=False)),
                ('completed_at', models.DateTimeField(blank=True, null=True)),
                ('units_donated', models.PositiveSmallIntegerField(default=0, help_text='Units of blood donated (usually 1 unit = 450ml)')),
                ('reminder_sent_at', models.DateTimeField(blank=True, help_text='When reminder notification was sent', null=True)),
                ('booked_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('donor', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='appointments', to=settings.AUTH_USER_MODEL)),
                ('slot', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='appointments', to='appointments.appointmentslot')),
            ],
            options={
                'ordering': ['-booked_at'],
                'unique_together': {('donor', 'slot')},
            },
        ),
        migrations.CreateModel(
            name='HealthQuestionnaire',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('has_fever', models.BooleanField(default=False)),
                ('has_cold_or_cough', models.BooleanField(default=False)),
                ('has_high_blood_pressure', models.BooleanField(default=False)),
                ('has_diabetes', models.BooleanField(default=False)),
                ('has_heart_condition', models.BooleanField(default=False)),
                ('has_cancer', models.BooleanField(default=False)),
                ('has_hiv_or_aids', models.BooleanField(default=False)),
                ('has_hepatitis', models.BooleanField(default=False)),
                ('has_bleeding_disorder', models.BooleanField(default=False)),
                ('is_pregnant', models.BooleanField(default=False)),
                ('is_breastfeeding', models.BooleanField(default=False)),
                ('recent_tattoo_or_piercing', models.BooleanField(default=False, help_text='In last 3 months')),
                ('recent_surgery', models.BooleanField(default=False, help_text='In last 6 months')),
                ('recent_blood_transfusion', models.BooleanField(default=False, help_text='In last 1 year')),
                ('recent_vaccination', models.BooleanField(default=False, help_text='In last 2 weeks')),
                ('takes_blood_thinners', models.BooleanField(default=False)),
                ('takes_antibiotics', models.BooleanField(default=False)),
                ('last_donation_date', models.DateField(blank=True, null=True)),
                ('weight_kg', models.FloatField(blank=True, null=True, validators=[django.core.validators.MinValueValidator(50.0)])),
                ('hemoglobin_level', models.FloatField(blank=True, null=True)),
                ('additional_notes', models.TextField(blank=True)),
                ('is_eligible', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('appointment', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='health_questionnaire', to='appointments.appointment')),
            ],
            options={
                'verbose_name_plural': 'Health Questionnaires',
            },
        ),
        migrations.AddIndex(
            model_name='appointmentslot',
            index=models.Index(fields=['date', 'city', 'status'], name='appointments_appointmentslot_date_city_status_idx'),
        ),
        migrations.AddIndex(
            model_name='appointment',
            index=models.Index(fields=['donor', 'status'], name='appointments_appointment_donor_status_idx'),
        ),
        migrations.AddIndex(
            model_name='appointment',
            index=models.Index(fields=['slot', 'status'], name='appointments_appointment_slot_status_idx'),
        ),
    ]
