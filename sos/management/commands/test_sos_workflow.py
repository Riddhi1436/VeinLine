"""
Management command to test SOS workflow: Create SOS request and send SMS to donors.
Usage: python manage.py test_sos_workflow --patient=<patient_id> --blood-group=O+ --city=Bangalore
"""

import logging
from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model
from sos.models import SOSRequest, SOSPriority, SOSStatus
from sos.services import match_donors_for_request
from core.services.sms import send_sms

User = get_user_model()
logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Create an SOS request and send SMS notifications to matching donors'

    def add_arguments(self, parser):
        parser.add_argument('--patient', type=int, help='Patient user ID')
        parser.add_argument('--blood-group', type=str, default='O+', help='Blood group needed (default: O+)')
        parser.add_argument('--city', type=str, default='Bangalore', help='City (default: Bangalore)')
        parser.add_argument('--area', type=str, default='', help='Area (optional)')
        parser.add_argument('--units', type=int, default=1, help='Units needed (default: 1)')
        parser.add_argument('--hospital', type=str, default='', help='Hospital name (optional)')
        parser.add_argument('--priority', type=str, default='normal', 
                          choices=['normal', 'urgent', 'critical'],
                          help='Priority level (default: normal)')
        parser.add_argument('--message', type=str, default='', help='Additional message (optional)')

    def handle(self, *args, **options):
        # Get patient
        patient_id = options.get('patient')
        if not patient_id:
            raise CommandError('--patient is required')
        
        try:
            patient = User.objects.get(id=patient_id)
        except User.DoesNotExist:
            raise CommandError(f'Patient with ID {patient_id} not found')

        # Create SOS request
        self.stdout.write(f'Creating SOS request for patient {patient.username}...')
        
        sos_req = SOSRequest.objects.create(
            requester=patient,
            blood_group_needed=options['blood_group'],
            units_needed=options['units'],
            city=options['city'],
            area=options['area'],
            hospital_name=options['hospital'],
            message=options['message'],
            status=SOSStatus.OPEN,
            priority=options['priority'],
        )
        
        self.stdout.write(self.style.SUCCESS(f'✓ SOS request created: #{sos_req.id}'))
        self.stdout.write(f'  Blood Group: {sos_req.blood_group_needed}')
        self.stdout.write(f'  Units: {sos_req.units_needed}')
        self.stdout.write(f'  Location: {sos_req.city}, {sos_req.area}')
        self.stdout.write(f'  Priority: {sos_req.priority}')
        self.stdout.write(f'  SMS Token: {sos_req.sms_reply_token}')

        # Find matching donors
        self.stdout.write('\nSearching for matching donors...')
        donors = match_donors_for_request(sos_req, limit=50)
        donors_list = list(donors)
        
        if not donors_list:
            self.stdout.write(self.style.WARNING('No matching donors found'))
            return

        self.stdout.write(self.style.SUCCESS(f'✓ Found {len(donors_list)} matching donors'))

        # Send SMS to each donor
        self.stdout.write('\nSending SMS notifications...')
        sms_message = (
            f"VeinLine SOS: Need {sos_req.blood_group_needed} blood in {sos_req.city}. "
            f"Reply: YES {sos_req.sms_reply_token} or NO {sos_req.sms_reply_token}."
        )

        sms_success = 0
        sms_failed = 0

        for donor in donors_list:
            phone = getattr(getattr(donor.user, 'profile', None), 'phone_e164', '')
            
            if not phone:
                self.stdout.write(f'  ⚠ {donor.full_name}: No phone number')
                sms_failed += 1
                continue

            try:
                result = send_sms(phone, sms_message)
                if result.get('ok'):
                    self.stdout.write(self.style.SUCCESS(f'  ✓ {donor.full_name}: SMS sent to {phone}'))
                    sms_success += 1
                else:
                    self.stdout.write(self.style.WARNING(
                        f'  ✗ {donor.full_name}: SMS skipped - {result.get("reason", "unknown")}'
                    ))
                    sms_failed += 1
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'  ✗ {donor.full_name}: Error - {str(e)}'))
                sms_failed += 1

        self.stdout.write('\n' + '='*60)
        self.stdout.write(self.style.SUCCESS(f'SOS Workflow Complete!'))
        self.stdout.write(f'SMS Sent: {sms_success}/{len(donors_list)}')
        if sms_failed > 0:
            self.stdout.write(self.style.WARNING(f'SMS Failed/Skipped: {sms_failed}/{len(donors_list)}'))
