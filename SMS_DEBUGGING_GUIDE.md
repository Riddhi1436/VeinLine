# 🔧 SOS SMS Not Working - Diagnosis & Fix Guide

## Problem
When a patient creates an SOS request, donors don't receive SMS notifications.

## Root Causes to Check

### 1. **SMS API Key Not Configured** ⚠️
The SMS service needs `VEINLINE_SMS_API_KEY` set in your environment.

**Fix:**
- Add to `.env` file:
  ```
  VEINLINE_SMS_API_KEY=your_fast2sms_or_textlocal_api_key
  VEINLINE_SMS_PROVIDER=fast2sms  # or textlocal
  VEINLINE_SMS_SENDER=VEINLN
  ```

### 2. **Donors Don't Have Phone Numbers** 👤
Donors must have their phone numbers in E.164 format (e.g., `+919876543210`) in their profile.

**Check:**
- Donors go to Profile → Add Phone Number
- Phone must be stored in `phone_e164` field
- Must be E.164 format with country code

### 3. **No Available Donors in the Same City** 🏙️
The matching algorithm requires:
- Donor must be in the **same city** as SOS request (case-sensitive)
- Donor's `is_available` must be `True`
- Donor must have compatible blood group

**Check:**
- Donors mark themselves as "Available" in profile
- Patient creating SOS enters exact city name
- Donor blood group matches SOS blood group needed

### 4. **Blood Group Mismatch** 🩸
Donor blood groups must be compatible with the needed blood group.

**Compatibility:**
- O- can donate to anyone
- O+ can donate to O+, A+, B+, AB+
- A- can donate to A-, AB-
- A+ can donate to A+, AB+
- B- can donate to B-, AB-
- B+ can donate to B+, AB+
- AB- can donate to AB-
- AB+ can donate to AB+

## Debugging Steps

### Step 1: Run Diagnostic Check
```bash
python manage.py shell
exec(open('check_sms_debug.py').read())
```

This will show:
- ✅/❌ SMS configuration status
- How many donors exist with phone numbers
- Available donors by city and blood group
- Recent SOS requests
- Test SMS sending

### Step 2: Check Django Logs
Look for errors in your Django logs for:
- `[SOS #X] Starting donor matching` - Should show matching started
- `[SOS #X] Found N matching donors` - Should show donors found
- `[SOS #X] Sending SMS to donor_name` - Should show SMS being sent
- `[SOS #X] ✓ SMS sent to donor_name` - SMS successful
- `[SOS #X] ✗ SMS failed for donor_name` - SMS failed with reason

### Step 3: Create Test Data
If no donors exist, create test donors:
```bash
python manage.py shell
```

```python
from django.contrib.auth.models import User
from accounts.models import Profile
from donations.models import DonorDetails

# Create test donor
user = User.objects.create_user(
    username='testdonor1',
    email='donor@test.com',
    password='testpass123'
)

# Add phone and profile
profile = user.profile  # Should auto-create via signal
profile.phone_e164 = '+919876543210'  # Change to real number or test number
profile.save()

# Add donor details
donor = DonorDetails.objects.create(
    user=user,
    blood_group='O+',
    city='Mumbai',  # Must match SOS city exactly
    area='Bandra',
    is_available=True,  # Important: must be True
    medical_history='None'
)
print(f"Created donor: {donor.user.username} in {donor.city}")
```

### Step 4: Test SOS Creation
1. Log in as patient
2. Go to Patient Dashboard
3. Click "🚨 Create SOS" button
4. Fill form:
   - Blood Group: O+ (or matching donor's group)
   - Units: 1-5
   - City: Same city as donor (e.g., "Mumbai")
   - Priority: Normal
   - Hospital: Any hospital name
5. Submit

### Step 5: Check Results
After submitting SOS:
1. **UI Feedback:** Should see success message like:
   ```
   ✅ Found 2 matching donors. Notifications sent to 2 donors.
   ```

2. **Check SMS Logs:**
   ```
   [SOS #123] Found 2 matching donors
   [SOS #123] Sending SMS to testdonor1 (+919876543210)
   [SOS #123] ✓ SMS sent to testdonor1
   [SOS #123] Sending SMS to testdonor2 (+919876543211)
   [SOS #123] ✓ SMS sent to testdonor2
   ```

3. **Verify Database:**
   ```python
   from sos.models import SOSRequest, SOSResponse
   sos = SOSRequest.objects.latest('created_at')
   print(f"SOS #{sos.id}: {sos.blood_group_needed} in {sos.city}")
   print(f"Responses: {sos.responses.count()}")
   for resp in sos.responses.all():
       print(f"  - {resp.donor.username}: {resp.response}")
   ```

## Common Issues & Solutions

| Issue | Cause | Solution |
|-------|-------|----------|
| "No matching donors found" | No available donors in city | Create donors or mark existing as available |
| "Found donors but SMS failed" | SMS API key not set | Set `VEINLINE_SMS_API_KEY` in .env |
| "Found donors but 0 notifications" | Donors have no phone number | Ask donors to add phone to profile |
| SMS returns error 400/401 | Wrong API key or provider | Check API key, verify provider is correct |
| SMS not received on phone | Provider issue or wrong number format | Verify phone is E.164 format (+country code) |

## Files Modified for Debugging

1. **webui/views.py** - Added detailed logging to `CreateSOSView`:
   - Shows which donors are found
   - Shows SMS being sent to each donor
   - Shows SMS success/failure for each donor
   - Shows donors with missing phone numbers

2. **check_sms_debug.py** - New diagnostic script:
   - Checks SMS configuration
   - Lists donors and phone numbers
   - Shows available donors by city
   - Tests SMS sending
   - Shows recent SOS requests

## Environment Setup

Add these to your `.env` file:

```env
# SMS Configuration
VEINLINE_SMS_API_KEY=your_api_key_here
VEINLINE_SMS_PROVIDER=fast2sms
VEINLINE_SMS_SENDER=VEINLN

# Django Settings
DEBUG=True
SECRET_KEY=your_secret_key
DATABASE_URL=sqlite:///db.sqlite3
ALLOWED_HOSTS=localhost,127.0.0.1

# Email (for fallback notifications)
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
```

## SMS Providers

### Fast2SMS
- **Website:** https://www.fast2sms.com
- **Plan:** DLT Route for business messages
- **API Key:** Get from dashboard after login
- **Phone Format:** Digits only (no +) or E.164 with +

### Textlocal
- **Website:** https://www.textlocal.in
- **Plan:** Business plan for higher volumes
- **API Key:** Get from Account Settings
- **Phone Format:** Digits only (no +) or E.164 with +

## Testing Checklist

- [ ] VEINLINE_SMS_API_KEY is set in .env or settings
- [ ] VEINLINE_SMS_PROVIDER is set (fast2sms or textlocal)
- [ ] At least 2 test donors created with phones
- [ ] Test donors have is_available = True
- [ ] Test donors have phone_e164 in E.164 format
- [ ] Test donors are in the same city
- [ ] Patient account created and logged in
- [ ] Diagnostic script runs without errors
- [ ] SOS form appears on patient dashboard
- [ ] SOS submission shows success message
- [ ] Django logs show SMS being sent
- [ ] SMS received on test donor's phone (if real API key)

## Need Help?

Check logs with:
```bash
tail -f logs/django.log | grep "SOS"
```

Or in Django shell:
```python
from django.contrib.auth.models import User
from sos.models import SOSRequest

user = User.objects.get(username='patient_username')
sos = SOSRequest.objects.filter(requester=user).latest('created_at')
print(f"SOS: {sos}")
print(f"Responses: {list(sos.responses.all())}")
```

---
**Last Updated:** 2024
**Version:** 1.0
