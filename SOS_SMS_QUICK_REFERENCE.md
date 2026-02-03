# VeinLine SOS SMS - Quick Reference

## 🚀 Getting Started (5 minutes)

### 1. Set Environment Variable
```bash
# Edit .env or export in terminal
export SMS_API_KEY=your_api_key_from_fast2sms
export SMS_PROVIDER=fast2sms
```

### 2. Run Test
```bash
python test_sos_sms_workflow.py
```

Expected output:
```
✓ SOS Request created: #1
✓ Found 3 matching donors
✓ SMS Sent: 3
```

### 3. Create SOS via API
```bash
# 1. Login and get token
curl -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"username": "patient1", "password": "pass"}'

# 2. Create SOS
curl -X POST http://localhost:8000/api/sos/requests/ \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "blood_group_needed": "O+",
    "units_needed": 2,
    "city": "Bangalore",
    "priority": "urgent"
  }'

# 3. Send SMS to matching donors
curl -X POST http://localhost:8000/api/sos/requests/1/match/ \
  -H "Authorization: Bearer <token>"
```

## 🔑 Key Concepts

| Term | Meaning |
|------|---------|
| SOS Request | Emergency blood request from patient |
| SOS Response | Donor's response (yes/no/pending) |
| Match | Find compatible donors in same city |
| sms_reply_token | Token for SMS replies (unique per request) |
| phone_e164 | Phone in E.164 format (+<country><number>) |

## 🛠️ Common Tasks

### Create Test Donor
```bash
python manage.py shell

from django.contrib.auth import get_user_model
from accounts.models import Profile, UserRole
from donations.models import DonorDetails

User = get_user_model()

# Create user
user = User.objects.create_user(username='donor1', password='pass')

# Add profile with phone
Profile.objects.create(
    user=user,
    role=UserRole.DONOR,
    city='Bangalore',
    phone_e164='+919876543210'
)

# Add donor details
DonorDetails.objects.create(
    user=user,
    full_name='John Doe',
    age=25,
    blood_group='O+',
    city='Bangalore',
    is_available=True
)
```

### Create Test SOS
```bash
from django.contrib.auth import get_user_model
from sos.models import SOSRequest, SOSStatus, SOSPriority

User = get_user_model()
patient = User.objects.get(username='patient1')

sos = SOSRequest.objects.create(
    requester=patient,
    blood_group_needed='O+',
    units_needed=2,
    city='Bangalore',
    priority=SOSPriority.URGENT,
    status=SOSStatus.OPEN
)
```

### Test SMS Sending
```bash
from core.services.sms import send_sms

result = send_sms('+919876543210', 'Test message')
print(result)
# Output: {'ok': True, 'provider': 'fast2sms', 'response': {...}}
```

### Check Donor-Patient Connection
```bash
from sos.models import SOSResponse

# Get all responses for an SOS request
responses = SOSResponse.objects.filter(request_id=1)

for r in responses:
    print(f"Donor: {r.donor.username}")
    print(f"Response: {r.response}")
    print(f"Channel: {r.channel}")
    print(f"Consented to share: {r.donor_consented_to_share_contact}")
```

## 🐛 Quick Troubleshooting

| Problem | Solution |
|---------|----------|
| SMS not sending | Check if SMS_API_KEY is set: `echo $SMS_API_KEY` |
| No donors found | Verify city matches exactly (case-sensitive) |
| Phone number error | Ensure E.164 format: +919876543210 |
| API returns 403 | Check user role is 'patient' for creating SOS |
| SMS marked skipped | SMS_API_KEY is empty or missing |

## 📱 SMS Message Format

Patient sends SOS → System sends SMS to donors:

```
VeinLine SOS: Need O+ blood in Bangalore. 
Reply: YES abc123xyz or NO abc123xyz.
(Optional consent: YES SHARE abc123xyz)
```

Donor replies:
- `YES abc123xyz` → Accepts to donate
- `NO abc123xyz` → Cannot donate
- `YES SHARE abc123xyz` → Accept + share contact

## 📊 Database Relationships

```
Patient User
├── Profile (role='patient', phone_e164)
└── SOSRequest (blood_group, city, sms_reply_token)
    └── SOSResponse (per donor)
        └── Donor User
            ├── Profile (role='donor', phone_e164)
            └── DonorDetails (blood_group, city, is_available)
```

## 🎯 Workflow Steps

1. **Patient creates SOS**
   - Specify blood group, location, priority
   - System generates sms_reply_token

2. **Patient triggers matching**
   - POST `/api/sos/requests/{id}/match/`
   - System finds compatible donors in same city

3. **System sends SMS**
   - Each matching donor receives SMS
   - SOSResponse record created (pending)
   - Includes sms_reply_token for replies

4. **Donor responds**
   - Reply via SMS or web interface
   - SOSResponse updated (yes/no)
   - Can consent to share contact

5. **Patient reveals contact**
   - If donor consented
   - Patient can call/message donor directly

## 🔧 Configuration Options

### settings.py options:
```python
VEINLINE_SMS_PROVIDER = 'fast2sms'  # or 'textlocal'
VEINLINE_SMS_API_KEY = 'your_key'
VEINLINE_SMS_SENDER = 'VEINLN'
VEINLINE_CITY_MATCH_STRICT = True   # Exact city match required
```

## 📞 SMS Providers

### Fast2SMS (India)
- Website: https://www.fast2sms.com
- Good for: India-focused apps
- Format: Digits only (no +)

### Textlocal
- Website: https://www.textlocal.in
- Good for: Global reach
- Format: Digits only (no +)

## 🔐 Security

- ✅ Phone hidden unless donor consents
- ✅ Token-based SMS replies (no passwords)
- ✅ Unique token per SOS request
- ✅ E.164 phone validation
- ✅ Role-based access control

## 📚 Documentation Files

- `SOS_SMS_SETUP_GUIDE.md` - Comprehensive setup
- `SOS_SMS_QUICK_SETUP.md` - Step-by-step checklist
- `SOS_SMS_IMPLEMENTATION_SUMMARY.md` - Technical details
- `SOS_SMS_QUICK_REFERENCE.md` - This file!

## 🚀 Next Steps

1. [ ] Configure SMS_API_KEY
2. [ ] Run test script
3. [ ] Create donor accounts with phone numbers
4. [ ] Create SOS request via API
5. [ ] Verify SMS sent successfully
6. [ ] Test donor response workflow
7. [ ] Monitor SMS delivery

## 💡 Pro Tips

**Tip 1: Use management command for bulk testing**
```bash
python manage.py test_sos_workflow --patient=1 --blood-group=O+ --city=Bangalore
```

**Tip 2: Check logs for debugging**
```bash
python manage.py shell
>>> import logging
>>> logging.basicConfig(level=logging.DEBUG)
>>> from core.services.sms import send_sms
>>> send_sms('+919876543210', 'test')
```

**Tip 3: Verify phone numbers**
```bash
python manage.py shell
>>> from accounts.models import Profile
>>> Profile.objects.filter(role='donor').exclude(phone_e164='').count()
```

**Tip 4: Test SMS provider API directly**
Visit your SMS provider dashboard and send test SMS to verify account is working.

## ⚡ Performance

- **SMS Timeout**: 20 seconds per SMS
- **Donor Limit**: 50 donors per match (can increase)
- **Atomic**: All SMS to donors in single transaction
- **Fallback**: Email sent if SMS fails

## 🆘 Emergency Debug

```bash
# Full diagnostic
python manage.py shell
from django.conf import settings
from django.contrib.auth import get_user_model
from accounts.models import Profile
from donations.models import DonorDetails
from sos.models import SOSRequest

# Check config
print("API Key set:", bool(settings.VEINLINE_SMS_API_KEY))
print("Provider:", settings.VEINLINE_SMS_PROVIDER)

# Check users
print("Donors with phone:", Profile.objects.filter(role='donor', phone_e164__isnull=False).count())

# Check SOS
print("Open SOS requests:", SOSRequest.objects.filter(status='open').count())

# Test SMS
from core.services.sms import send_sms
result = send_sms('+919876543210', 'test')
print("SMS Result:", result)
```

---

**Quick Links**:
- Comprehensive Guide: [SOS_SMS_SETUP_GUIDE.md](SOS_SMS_SETUP_GUIDE.md)
- Setup Checklist: [SOS_SMS_QUICK_SETUP.md](SOS_SMS_QUICK_SETUP.md)
- Implementation Details: [SOS_SMS_IMPLEMENTATION_SUMMARY.md](SOS_SMS_IMPLEMENTATION_SUMMARY.md)
