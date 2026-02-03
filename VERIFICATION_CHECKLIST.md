# ✅ SOS SMS Fix - Verification Checklist

## Pre-Implementation Checks
- [ ] Django server can start without errors
- [ ] Database is accessible
- [ ] All migrations applied
- [ ] Static files configured

## Code Implementation Checks

### webui/views.py
- [ ] Logging import added: `import logging`
- [ ] Logger created: `logger = logging.getLogger(__name__)`
- [ ] No syntax errors in CreateSOSView
- [ ] Try-catch blocks have logging
- [ ] Error messages include SOS ID for tracking
- [ ] Success messages show counts (found, sent, failed, missing)

### check_sms_debug.py
- [ ] File created and readable
- [ ] No syntax errors
- [ ] Checks VEINLINE_SMS_API_KEY
- [ ] Checks VEINLINE_SMS_PROVIDER
- [ ] Lists donors with phones
- [ ] Shows available donors by city
- [ ] Tests SMS sending
- [ ] Shows recommendations

### Documentation
- [ ] START_HERE.md created
- [ ] SMS_DEBUGGING_GUIDE.md created
- [ ] SOS_SMS_QUICK_TEST.md created
- [ ] SOS_SMS_ARCHITECTURE.md created
- [ ] IMPLEMENTATION_STATUS.md created
- [ ] FIX_REPORT.md created
- [ ] check_sms_debug.py created

## Environment Configuration
- [ ] .env file exists
- [ ] VEINLINE_SMS_API_KEY set (or empty for dev)
- [ ] VEINLINE_SMS_PROVIDER set to 'fast2sms' or 'textlocal'
- [ ] VEINLINE_SMS_SENDER set to 'VEINLN'
- [ ] Other required settings configured

## Database Setup
- [ ] Admin user created
- [ ] At least 1 patient user created
- [ ] At least 1 donor user created
- [ ] Donor marked as is_available=True
- [ ] Donor has phone_e164 set
- [ ] Patient and donor are in same city

## Testing - Phase 1: Configuration

```bash
# Command
python manage.py shell
exec(open('check_sms_debug.py').read())

# Check
□ SMS_PROVIDER: Shows 'fast2sms' or 'textlocal'
□ SMS_API_KEY: Shows '✅ SET' or says not set
□ Total users with phone: Shows > 0 (or expected)
□ Total donors: Shows > 0
□ Available donors with phone: Shows > 0 (ideally)
□ No errors in output
```

## Testing - Phase 2: Data Creation

```bash
# Command
python manage.py shell

# Create Test Data (Python commands)
from django.contrib.auth.models import User
from donations.models import DonorDetails

# Create donor
user = User.objects.create_user(username='testdonor1', password='test123')
user.profile.phone_e164 = '+919876543210'
user.profile.save()
donor = DonorDetails.objects.create(
    user=user,
    blood_group='O+',
    city='Mumbai',
    area='Bandra',
    is_available=True,
    medical_history='None'
)

# Check
□ No errors during creation
□ Donor created in database
□ Donor has all required fields
□ User has profile with phone
```

## Testing - Phase 3: SOS Creation

```bash
# Steps
1. Start server: python manage.py runserver
2. Open browser: http://localhost:8000
3. Login as patient
4. Go to /patient-dashboard
5. Click "🚨 Create SOS"
6. Fill form:
   □ Blood Group: O+
   □ Units: 2
   □ City: Mumbai (must match donor city)
   □ Area: Bandra (optional)
   □ Hospital: Any Name
   □ Priority: Normal
   □ Message: Test message
7. Submit form

# Check Results
□ Form submitted without errors
□ Redirected to dashboard
□ Success message shown
□ Message shows "Found X matching donors"
□ No error messages displayed
```

## Testing - Phase 4: Log Verification

```bash
# Check Terminal/Logs
Look for these messages (in order):
□ [SOS #X] Created by patient_username for O+ in Mumbai
□ [SOS #1] Starting donor matching for O+ in Mumbai
□ [SOS #1] Found Y matching donors
□ [SOS #1] Sending SMS to donor1 (+919876543210)
□ [SOS #1] ✓ SMS sent to donor1 (or ✗ with reason)

# If any line is missing
Check the logs directory
Look for errors in Django console output
```

## Testing - Phase 5: Database Verification

```bash
# Command
python manage.py shell

# Check SOS was created
from sos.models import SOSRequest
sos = SOSRequest.objects.latest('created_at')

□ sos.id is not None
□ sos.requester.username is patient username
□ sos.blood_group_needed is 'O+'
□ sos.city is 'Mumbai'
□ sos.status is 'open'

# Check responses were created
responses = sos.responses.all()
□ responses.count() >= 1 (should have response for each matched donor)
□ Each response has donor set
□ Each response has response='pending'
□ Each response has channel='sms'
```

## Testing - Phase 6: SMS Sending Verification (if real API)

```bash
# Only if using real SMS_API_KEY
□ Check real phone for SMS
□ SMS received with SOS details
□ Phone number in SOS matches (last 4 digits)
□ Hospital name in message
□ Blood group in message

# If SMS not received
□ Check API key is correct
□ Check phone format is E.164
□ Check SMS provider account has credits
□ Check spam folder
```

## Common Issues - Diagnosis

### No "Found X matching donors" message

```bash
# Check
python manage.py shell
from donations.models import DonorDetails
from sos.services import compatible_donor_groups

# 1. Check donors exist
donors = DonorDetails.objects.all()
□ donors.count() > 0 (if 0, create test donors)

# 2. Check donors available
available = DonorDetails.objects.filter(is_available=True)
□ available.count() > 0 (if 0, mark some as available)

# 3. Check donors have phone
with_phone = DonorDetails.objects.filter(
    user__profile__phone_e164__isnull=False
).exclude(user__profile__phone_e164='')
□ with_phone.count() > 0 (if 0, add phones)

# 4. Check city match
for d in DonorDetails.objects.all():
    print(f"{d.user.username}: {d.city}")
□ At least one donor city matches SOS city (exact, case-insensitive)

# 5. Check blood group compatibility
groups = compatible_donor_groups('O+')
print(groups)
□ Should show: {'O-', 'O+'}
□ Check if donor blood group in this set
```

### SMS shows "Sending SMS to X" but no "✓ SMS sent"

```bash
# Check logs for error
grep "✗ SMS failed" logs/django.log

# Common errors and fixes
□ "invalid_phone" → Phone format wrong (must be +country code)
□ "provider_error" → API key wrong or expired
□ "timeout" → Network issue
□ "skipped: missing_api_key" → VEINLINE_SMS_API_KEY not set

# Fix based on error, then retry
```

### SOS created but says "0 notifications sent"

```bash
# Check
python manage.py shell
from donations.models import DonorDetails

# List all donors and their phones
for d in DonorDetails.objects.all():
    phone = getattr(d.user.profile, 'phone_e164', 'NO PHONE')
    print(f"{d.user.username}: {phone} (Available: {d.is_available})")

# Fix: Add phones to donors
d = DonorDetails.objects.get(user__username='testdonor1')
d.user.profile.phone_e164 = '+919876543210'
d.user.profile.save()
```

## Rollback Plan (if needed)

```bash
# If need to revert changes to webui/views.py
git checkout webui/views.py

# But first, save the improved version
cp webui/views.py webui/views.py.improved

# Then revert
git checkout webui/views.py
```

## Success Confirmation

✅ **SMS is working when ALL of these are true:**

```
□ Diagnostic script runs without errors
□ Shows "✅ SET" for SMS_API_KEY (or empty is OK for dev)
□ Shows available donors with phones
□ SOS form submission shows "Found X matching donors"
□ Django logs show [SOS #X] messages
□ Logs show "✓ SMS sent to donor_name"
□ SOSResponse records created in database
□ Patient sees success message on dashboard
```

## Next Phase - Ready When:

✅ All checkboxes above are filled

✅ No errors in logs

✅ SOS successfully created

✅ Donors found and matched

✅ SMS shows as sent in logs

**Next Phase:** Implement donor SMS reply handling (YES/NO responses)

## Support Resources

| Issue | See |
|-------|-----|
| General troubleshooting | SMS_DEBUGGING_GUIDE.md |
| Quick setup | SOS_SMS_QUICK_TEST.md |
| How system works | SOS_SMS_ARCHITECTURE.md |
| Current status | IMPLEMENTATION_STATUS.md |
| This fix | FIX_REPORT.md |
| How to start | START_HERE.md |
| Run first | check_sms_debug.py |

## Final Checklist

Before declaring done:

- [ ] All documentation created
- [ ] Code has no syntax errors  
- [ ] Diagnostic script works
- [ ] Test donor can be created
- [ ] SOS form accessible
- [ ] SOS creation succeeds
- [ ] Logs show correct flow
- [ ] No exceptions thrown
- [ ] Patient sees success message
- [ ] All files listed in manifest

---

## Files Modified/Created

### Modified:
- ✅ webui/views.py (CreateSOSView enhanced)

### Created:
- ✅ check_sms_debug.py
- ✅ START_HERE.md
- ✅ SMS_DEBUGGING_GUIDE.md
- ✅ SOS_SMS_QUICK_TEST.md
- ✅ SOS_SMS_ARCHITECTURE.md
- ✅ IMPLEMENTATION_STATUS.md
- ✅ FIX_REPORT.md
- ✅ VERIFICATION_CHECKLIST.md (this file)

---

**Start with:** `python manage.py shell < check_sms_debug.py`

**Then follow:** SMS_DEBUGGING_GUIDE.md (if issues) or SOS_SMS_QUICK_TEST.md (quick test)

**Status:** Ready for verification testing

---
**Version:** 1.0
**Date:** 2024
**Last Checked:** Today
