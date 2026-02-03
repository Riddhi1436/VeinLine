# 📱 Quick Start: Test SOS SMS Feature

## 30-Minute Setup

### Step 1: Configure SMS (2 min)
Add to `.env` file:
```env
VEINLINE_SMS_API_KEY=your_api_key_from_fast2sms
VEINLINE_SMS_PROVIDER=fast2sms
VEINLINE_SMS_SENDER=VEINLN
```

Or for development without real SMS:
```env
VEINLINE_SMS_API_KEY=
VEINLINE_SMS_PROVIDER=fast2sms
```
(Empty key = SMS will be logged but not sent)

### Step 2: Start Server (1 min)
```bash
python manage.py runserver
```

### Step 3: Create Test Donor (10 min)

**Option A: Via Django Shell**
```bash
python manage.py shell
```
```python
from django.contrib.auth.models import User
from donations.models import DonorDetails

# Create donor user
user = User.objects.create_user(
    username='donor_mumbai_o_plus',
    email='donor@test.com',
    password='Test@123'
)

# Add phone number to profile
user.profile.phone_e164 = '+919876543210'  # Add your test number here
user.profile.save()

# Create donor details
donor = DonorDetails.objects.create(
    user=user,
    blood_group='O+',
    city='Mumbai',  # Important: must match patient's city
    area='Bandra',
    is_available=True,  # Critical: must be True
    medical_history='None'
)

print(f"✅ Created donor: {donor.user.username}")
print(f"   City: {donor.city}")
print(f"   Blood Group: {donor.blood_group}")
print(f"   Available: {donor.is_available}")
print(f"   Phone: {donor.user.profile.phone_e164}")
```

**Option B: Via Django Admin**
1. Go to http://localhost:8000/admin
2. Create User: `admin / admin`
3. Go to Users → Add User
   - Username: `donor_mumbai_o_plus`
   - Password: `Test@123`
4. Go to Donor Details → Add Donor Detail
   - User: `donor_mumbai_o_plus`
   - Blood Group: `O+`
   - City: `Mumbai`
   - Area: `Bandra`
   - Is Available: ✅ Check
5. Edit User Profile
   - Phone E164: `+919876543210`

### Step 4: Create Test Patient (5 min)

```bash
python manage.py shell
```
```python
from django.contrib.auth.models import User

# Create patient user
user = User.objects.create_user(
    username='patient_mumbai',
    email='patient@test.com',
    password='Test@123'
)

# Mark as patient
user.groups.add('patient')  # Or set in profile

print(f"✅ Created patient: {user.username}")
```

Or register via web interface at http://localhost:8000/accounts/signup

### Step 5: Test SOS Feature (5 min)

1. **Login as Patient**
   - Go to http://localhost:8000
   - Login with patient credentials

2. **Create SOS**
   - Click "🚨 Create SOS" on dashboard
   - Fill form:
     ```
     Blood Group Needed: O+
     Units Needed: 2
     City: Mumbai          # MUST match donor's city
     Area: Andheri         # Optional
     Hospital: Lilavati    # Any name
     Priority: Normal
     Message: Emergency
     ```

3. **Submit**
   - Click "Create SOS Request"
   - Should see success message:
     ```
     ✅ Found 1 matching donors. Notifications sent to 1 donors.
     ```

### Step 6: Verify Results (3 min)

**Check Success Message**
- Patient dashboard should show:
  - SOS Request created
  - Count of donors notified
  - Count of SMS sent

**Check Django Logs**
```
[SOS #1] Created by patient_mumbai for O+ in Mumbai
[SOS #1] Starting donor matching for O+ in Mumbai
[SOS #1] Found 1 matching donors
[SOS #1] Sending SMS to donor_mumbai_o_plus (+919876543210)
[SOS #1] ✓ SMS sent to donor_mumbai_o_plus
```

**Check Database**
```bash
python manage.py shell
```
```python
from sos.models import SOSRequest, SOSResponse

# Get latest SOS
sos = SOSRequest.objects.latest('created_at')
print(f"SOS #{sos.id}")
print(f"  Requester: {sos.requester.username}")
print(f"  Blood Needed: {sos.blood_group_needed}")
print(f"  City: {sos.city}")
print(f"  Status: {sos.status}")
print(f"  Responses: {sos.responses.count()}")

# Check responses
for resp in sos.responses.all():
    print(f"    - {resp.donor.username}: {resp.response}")
```

## Troubleshooting

### Problem: "No matching donors found"

```bash
python manage.py shell
exec(open('check_sms_debug.py').read())
```

**Check:**
1. Donor exists: `DonorDetails.objects.all()`
2. Donor city matches (case-sensitive!): `donor.city == sos.city`
3. Donor is available: `donor.is_available == True`
4. Blood groups compatible: O+ donor can give to O+ patient

**Example Fix:**
```python
# Find the donor
donor = DonorDetails.objects.get(user__username='donor_mumbai_o_plus')

# Check attributes
print(f"Is Available: {donor.is_available}")  # Should be True
print(f"City: {donor.city}")                  # Should be 'Mumbai'
print(f"Blood Group: {donor.blood_group}")   # Should be 'O+'

# Fix if needed
donor.is_available = True
donor.city = 'Mumbai'  # Exact match with SOS city
donor.save()
```

### Problem: "Found donors but 0 notifications sent"

**Cause:** Donors have no phone numbers

```python
from donations.models import DonorDetails

# Check all donors
for donor in DonorDetails.objects.all():
    phone = getattr(donor.user.profile, 'phone_e164', '')
    print(f"{donor.user.username}: {phone or 'NO PHONE'}")

# Fix: Add phone to donor
donor = DonorDetails.objects.get(user__username='donor_mumbai_o_plus')
donor.user.profile.phone_e164 = '+919876543210'
donor.user.profile.save()
```

### Problem: SMS sent but not received

**Cause:** Wrong API key or phone format

```env
# Verify in .env:
VEINLINE_SMS_API_KEY=xxx      # Real API key from Fast2SMS
VEINLINE_SMS_PROVIDER=fast2sms
```

**Check phone format:**
```python
import re

phone = '+919876543210'

# Must be E.164 format
pattern = r'^\+[1-9]\d{1,14}$'
is_valid = re.match(pattern, phone) is not None
print(f"Phone {phone} valid E.164: {is_valid}")
```

## Blood Group Compatibility

| Recipient | Can receive from |
|-----------|-----------------|
| O- | O- |
| O+ | O-, O+ |
| A- | O-, A- |
| A+ | O-, O+, A-, A+ |
| B- | O-, B- |
| B+ | O-, O+, B-, B+ |
| AB- | O-, A-, B-, AB- |
| AB+ | O-, O+, A-, A+, B-, B+, AB-, AB+ |

## Example Full Workflow

```bash
# Terminal 1: Start server
python manage.py runserver

# Terminal 2: Setup data
python manage.py shell
```

```python
# Create donor
from django.contrib.auth.models import User
from donations.models import DonorDetails

donor_user = User.objects.create_user(username='donor1', password='test123')
donor_user.profile.phone_e164 = '+919876543210'
donor_user.profile.save()

DonorDetails.objects.create(
    user=donor_user,
    blood_group='O+',
    city='Mumbai',
    area='Bandra',
    is_available=True,
    medical_history='None'
)

# Create patient
patient_user = User.objects.create_user(username='patient1', password='test123')
patient_user.groups.add('patient')

print("✅ Setup complete!")
print(f"   Donor: donor1 / test123 (O+, Mumbai)")
print(f"   Patient: patient1 / test123 (Mumbai)")
```

```
# Then in browser:
1. Login as patient1
2. Go to http://localhost:8000/patient-dashboard
3. Click "🚨 Create SOS"
4. Fill: O+, 2 units, Mumbai, "Test"
5. Submit
6. See "✅ Found 1 matching donors. Notifications sent to 1"
```

## Files Modified for Debugging

| File | Change | Purpose |
|------|--------|---------|
| `webui/views.py` | Added logging to `CreateSOSView` | See SMS sending details |
| `check_sms_debug.py` | New diagnostic script | Check config and test SMS |
| `SMS_DEBUGGING_GUIDE.md` | Detailed troubleshooting | Fix common issues |

## Next Steps

After SOS SMS works:
1. Donors receive SMS with SOS details
2. Donors reply YES/NO
3. Patient gets notification of donor responses
4. In-app chat or call coordination

---
**Quick Links:**
- Admin: http://localhost:8000/admin
- Patient Dashboard: http://localhost:8000/patient-dashboard
- Create SOS Form: http://localhost:8000/sos/create/
- Django Shell: `python manage.py shell`
- Check Logs: `python manage.py shell < check_sms_debug.py`

**Need Help?** Check SMS_DEBUGGING_GUIDE.md for detailed solutions.
