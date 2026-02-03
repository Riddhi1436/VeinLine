# ✅ SOS SMS Verification Checklist

Use this checklist to verify that the SOS SMS feature is fully working.

## 🔧 Pre-Verification Setup

- [ ] SMS_API_KEY is set in .env or environment
- [ ] SMS_PROVIDER is set (fast2sms or textlocal)
- [ ] Database is migrated (`python manage.py migrate`)
- [ ] Django project starts without errors (`python manage.py runserver`)

## 📝 Step 1: Database & Configuration Check

### ✅ Configuration is correct
```bash
python manage.py shell
>>> from django.conf import settings
>>> bool(settings.VEINLINE_SMS_API_KEY)  # Should be True
True
>>> settings.VEINLINE_SMS_PROVIDER  # Should show provider
'fast2sms'
```
- [ ] SMS_API_KEY exists and is not empty
- [ ] SMS_PROVIDER is 'fast2sms' or 'textlocal'
- [ ] SMS_SENDER is set (default: 'VEINLN')

### ✅ Models exist and work
```bash
>>> from sos.models import SOSRequest, SOSResponse
>>> from donations.models import DonorDetails
>>> from accounts.models import Profile
>>> print("Models loaded successfully")
```
- [ ] All models import without errors
- [ ] Database tables exist (run `python manage.py migrate` if missing)

## 🧪 Step 2: Test SMS Sending

### ✅ SMS service works
```bash
python manage.py shell
>>> from core.services.sms import send_sms
>>> result = send_sms('+919876543210', 'VeinLine Test SMS')
>>> print(result)
```
- [ ] Returns a dictionary (not error)
- [ ] Shows 'ok', 'provider', and 'reason' fields
- [ ] If API key is set, should attempt to send

**Expected results:**
```python
# If SMS_API_KEY is set and provider is working:
{'ok': True, 'provider': 'fast2sms', 'response': {...}}

# If SMS_API_KEY is empty (dev mode):
{'ok': False, 'skipped': True, 'reason': 'missing_api_key'}
```
- [ ] Result follows expected format

## 👥 Step 3: Create Test Users

### ✅ Create test patient
```bash
python manage.py shell
>>> from django.contrib.auth import get_user_model
>>> from accounts.models import Profile, UserRole
>>> 
>>> User = get_user_model()
>>> patient = User.objects.create_user(
...     username='test_patient',
...     email='patient@test.com',
...     password='testpass123'
... )
>>> profile = Profile.objects.create(
...     user=patient,
...     role=UserRole.PATIENT,
...     city='Bangalore',
...     phone_e164='+919000000001'
... )
>>> print(f"Patient created: {patient.username}")
```
- [ ] Patient user created
- [ ] Patient profile created with phone_e164
- [ ] Patient city is set

### ✅ Create test donors
```bash
>>> from donations.models import DonorDetails, DonorStatistics
>>> 
>>> for i in range(1, 4):
...     donor = User.objects.create_user(
...         username=f'test_donor_{i}',
...         email=f'donor{i}@test.com',
...         password='testpass123'
...     )
...     Profile.objects.create(
...         user=donor,
...         role=UserRole.DONOR,
...         city='Bangalore',
...         phone_e164=f'+919000000{i:02d}'
...     )
...     DonorDetails.objects.create(
...         user=donor,
...         full_name=f'Donor {i}',
...         age=25,
...         blood_group='O+',
...         city='Bangalore',
...         is_available=True
...     )
...     DonorStatistics.objects.create(donor=donor)
... print("Donors created successfully")
```
- [ ] 3 donor users created
- [ ] Each donor has profile with phone_e164
- [ ] Each donor has DonorDetails with is_available=True
- [ ] All donors in 'Bangalore' city
- [ ] All donors have blood_group 'O+'

### ✅ Verify test data
```bash
>>> from accounts.models import Profile
>>> from donations.models import DonorDetails
>>> 
>>> print(f"Total donors: {Profile.objects.filter(role='donor').count()}")
>>> print(f"Donors with phone: {Profile.objects.filter(role='donor', phone_e164__isnull=False).count()}")
>>> print(f"Available donors: {DonorDetails.objects.filter(is_available=True).count()}")
>>> print(f"Donors in Bangalore: {DonorDetails.objects.filter(city='Bangalore').count()}")
```
- [ ] Total donors: >= 3
- [ ] Donors with phone: >= 3
- [ ] Available donors: >= 3
- [ ] Donors in Bangalore: >= 3

## 📋 Step 4: Test SOS Creation

### ✅ Create SOS request
```bash
>>> from sos.models import SOSRequest, SOSStatus, SOSPriority
>>> 
>>> sos = SOSRequest.objects.create(
...     requester=patient,
...     blood_group_needed='O+',
...     units_needed=2,
...     city='Bangalore',
...     area='Indiranagar',
...     hospital_name='Test Hospital',
...     priority=SOSPriority.URGENT,
...     status=SOSStatus.OPEN
... )
>>> print(f"SOS created: #{sos.id}")
>>> print(f"SMS Token: {sos.sms_reply_token}")
```
- [ ] SOS request created successfully
- [ ] SOS has unique ID
- [ ] sms_reply_token is generated and not empty
- [ ] SOS status is 'open'

## 🔍 Step 5: Test Donor Matching

### ✅ Match donors
```bash
>>> from sos.services import match_donors_for_request
>>> 
>>> matched_donors = match_donors_for_request(sos, limit=50)
>>> matched_list = list(matched_donors)
>>> print(f"Matched donors: {len(matched_list)}")
>>> for d in matched_list:
...     print(f"  - {d.full_name} ({d.blood_group}) in {d.city}")
```
- [ ] Donors matched: >= 1 (should be 3)
- [ ] Matched donors show in list
- [ ] All matched donors are in Bangalore
- [ ] All matched donors have blood_group 'O+'
- [ ] All matched donors have is_available=True

## 📱 Step 6: Test SMS Sending

### ✅ Send SMS to donors (via code)
```bash
>>> from core.services.sms import send_sms
>>> 
>>> for donor in matched_list:
...     phone = getattr(getattr(donor.user, 'profile', None), 'phone_e164', '')
...     if phone:
...         message = f"Test SOS #{sos.id} for {sos.blood_group_needed}"
...         result = send_sms(phone, message)
...         status = "✓" if result.get('ok') else "✗"
...         print(f"{status} {donor.full_name} ({phone}): {result.get('reason', 'ok')}")
```
- [ ] Each donor phone is retrieved successfully
- [ ] SMS service called for each donor
- [ ] Result shows 'ok' or 'skipped' status

**Expected output (if API key set):**
```
✓ Donor 1 (+919000000001): ok
✓ Donor 2 (+919000000002): ok
✓ Donor 3 (+919000000003): ok
```

**Expected output (if API key not set):**
```
✗ Donor 1 (+919000000001): missing_api_key
✗ Donor 2 (+919000000002): missing_api_key
✗ Donor 3 (+919000000003): missing_api_key
```
- [ ] Result shows expected format

## 🔗 Step 7: Test SOSResponse Creation

### ✅ Create SOSResponse records
```bash
>>> from sos.models import SOSResponse, ResponseChoice, ResponseChannel
>>> 
>>> for donor in matched_list:
...     resp, created = SOSResponse.objects.get_or_create(
...         request=sos,
...         donor=donor.user,
...         defaults={'response': ResponseChoice.PENDING, 'channel': ResponseChannel.SMS}
...     )
...     status = "Created" if created else "Already exists"
...     print(f"{status}: {donor.full_name} -> Response #{resp.id}")
```
- [ ] SOSResponse created for each matched donor
- [ ] Response status is 'pending' initially
- [ ] Channel is 'sms'
- [ ] Unique constraint enforced (no duplicates)

### ✅ Verify SOSResponse records
```bash
>>> sos_responses = SOSResponse.objects.filter(request=sos)
>>> print(f"Total responses: {sos_responses.count()}")
>>> for resp in sos_responses:
...     print(f"  - {resp.donor.username}: {resp.response} via {resp.channel}")
```
- [ ] Total responses: >= 3
- [ ] All responses link to same SOS request
- [ ] All responses show channel='sms'
- [ ] All responses show response='pending'

## 🧪 Step 8: Automated Test Script

### ✅ Run full test script
```bash
python test_sos_sms_workflow.py
```

Expected output includes:
- [ ] Test title displayed
- [ ] Patient user created or found
- [ ] 3 donor users created or found
- [ ] Donor profiles created with phone numbers
- [ ] SOS request created (#1)
- [ ] 3 donors found and matched
- [ ] SMS results shown for each donor

Expected format:
```
==================================================
VeinLine SOS SMS Workflow Test
==================================================

[1] Creating test patient user...
✓ Created patient user: test_patient_sms
✓ Patient profile: patient in Bangalore

[2] Creating test donor users...
  ✓ Created donor user: test_donor_1
  ✓ Donor profile: +919000000101
  ...
  
[3] Creating SOS request...
✓ SOS Request created: #1
  Blood Group: O+
  ...

[4] Finding matching donors...
✓ Found 3 matching donors

[5] Creating SOSResponse records...
  ✓ SOSResponse Created: ...

[6] Sending SMS to matching donors...
  Sending to Donor One (+919000000101)...
    ✓ SMS sent successfully
  ...

==================================================
TEST SUMMARY
==================================================
SOS Request: #1 (O+ in Bangalore)
Matching Donors Found: 3
SMS Statistics:
  ✓ Sent: 3
  ⚠ Skipped: 0
  ✗ Failed: 0

✓ Test workflow completed successfully!
==================================================
```

- [ ] Script runs without Python errors
- [ ] All sections complete successfully
- [ ] Summary shows correct counts
- [ ] No fatal errors logged

## 📊 Step 9: Verify API Endpoints

### ✅ Test via Django shell
```bash
python manage.py shell
>>> from django.test import Client
>>> client = Client()
>>> 
>>> # Create auth token (if using token auth)
>>> # Then test endpoints...
```

Or use REST API client:

### ✅ List SOS requests
```bash
GET /api/sos/requests/
Authorization: Bearer <token>
```
- [ ] Returns status 200
- [ ] Returns list of SOS requests
- [ ] Your test SOS is in the list

### ✅ Get SOS details
```bash
GET /api/sos/requests/1/
Authorization: Bearer <token>
```
- [ ] Returns status 200
- [ ] Shows SOS #1 details
- [ ] sms_reply_token is included (not exposed to UI)

### ✅ List SOS responses
```bash
GET /api/sos/responses/
Authorization: Bearer <token>
```
- [ ] Returns status 200
- [ ] Shows SOSResponse records
- [ ] channel shows 'sms'

## 🚀 Step 10: Production Readiness Check

### ✅ Code quality
```bash
# Check for errors
python manage.py check

# Run migrations
python manage.py migrate

# Collect static files (if needed)
python manage.py collectstatic --noinput
```
- [ ] No errors in `python manage.py check`
- [ ] All migrations applied
- [ ] No compilation errors in Python files

### ✅ Settings verification
```bash
python manage.py shell
>>> from django.conf import settings
>>> print(f"DEBUG: {settings.DEBUG}")
>>> print(f"ALLOWED_HOSTS: {settings.ALLOWED_HOSTS}")
>>> print(f"SMS configured: {bool(settings.VEINLINE_SMS_API_KEY)}")
```
- [ ] SMS_API_KEY configured
- [ ] SMS_PROVIDER set
- [ ] Other Django settings correct

### ✅ Logging setup
- [ ] Logs directory exists
- [ ] Django logs configured
- [ ] SMS logs can be monitored

## 📞 Step 11: SMS Provider Verification

### ✅ Fast2SMS (if using)
- [ ] Log into https://www.fast2sms.com
- [ ] API key in settings matches dashboard key
- [ ] Account has SMS balance available
- [ ] SMS history shows sent messages (if sent with real key)
- [ ] Sender ID set to 'VEINLN' or configured value

### ✅ Textlocal (if using)
- [ ] Log into https://www.textlocal.in
- [ ] API key in settings matches dashboard key
- [ ] Account has SMS credits available
- [ ] SMS sent log shows recent messages
- [ ] Sender ID configured correctly

## 🎯 Final Verification

### ✅ All systems operational
- [ ] Database has SOS, SOSResponse, DonorDetails records
- [ ] SMS service returns proper responses
- [ ] Donor matching works
- [ ] SMS token is generated
- [ ] API endpoints return correct data
- [ ] No Python errors in logs

### ✅ Ready for production?
- [ ] All tests pass (23+ checkboxes checked)
- [ ] SMS API key is production key (if deployed)
- [ ] Donors have real phone numbers
- [ ] Error monitoring is set up
- [ ] Backup SMS provider configured (optional)
- [ ] Rate limiting configured (optional)
- [ ] Webhook for SMS replies configured (optional)

## 📋 Troubleshooting if Something Failed

| Symptom | Troubleshooting Step |
|---------|---------------------|
| SMS service returns error | Check API key and provider settings |
| No donors matched | Verify city name (case-sensitive), blood group, is_available=True |
| Phone format error | Ensure E.164 format: +919876543210 |
| Database error | Run `python manage.py migrate` |
| API returns 403 | Check user authentication and role permissions |
| SMS skipped | Check if SMS_API_KEY is set |

**For detailed troubleshooting:** See [SOS_SMS_TROUBLESHOOTING.md](SOS_SMS_TROUBLESHOOTING.md)

## ✅ Sign Off

Once all checkboxes are complete, sign here:

```
Date: _______________
Tester: _______________
Status: ☐ All tests passed ☐ Some tests failed (see notes)

Notes:
_________________________________________________
_________________________________________________
_________________________________________________
```

---

**You're Done!** 🎉

The SOS SMS feature is now verified and ready to use.

Next steps:
1. Deploy to production
2. Monitor SMS delivery
3. Test with real donors
4. Gather feedback
5. Iterate and improve

Good luck! 🩸
