# VeinLine SOS SMS - Quick Setup Checklist

## ✅ Prerequisites
- [ ] Django 5.1.6+ installed
- [ ] djangorestframework installed
- [ ] requests library installed (for HTTP calls to SMS providers)
- [ ] Database migrated (`python manage.py migrate`)

## ✅ Step 1: SMS Provider Setup

### Choose a Provider:
- [ ] **Fast2SMS** - https://www.fast2sms.com (India-focused)
- [ ] **Textlocal** - https://www.textlocal.in (Global)
- [ ] **Other**: ________________

### Get API Credentials:
- [ ] Sign up with chosen provider
- [ ] Get API Key
- [ ] Note down Sender ID (if needed)

## ✅ Step 2: Environment Configuration

### Update .env file:
```env
SMS_PROVIDER=fast2sms              # Or textlocal
SMS_API_KEY=your_actual_api_key    # Replace with real key
SMS_SENDER=VEINLN                  # Sender ID
```

### Verify in Django shell:
```bash
python manage.py shell
>>> from django.conf import settings
>>> settings.VEINLINE_SMS_API_KEY  # Should show your key
>>> settings.VEINLINE_SMS_PROVIDER  # Should show provider
```

## ✅ Step 3: Data Setup

### Create Patient User (if needed):
```bash
python manage.py createsuperuser  # Or use existing user
```

### Create Donor Users with Phone Numbers:
```bash
python manage.py shell
>>> from django.contrib.auth import get_user_model
>>> from accounts.models import Profile, UserRole
>>> from donations.models import DonorDetails

# Create donor user
user = get_user_model().objects.create_user(
    username='donor1',
    email='donor@test.com',
    password='testpass123'
)

# Add profile with phone
profile = Profile.objects.create(
    user=user,
    role=UserRole.DONOR,
    city='Bangalore',
    phone_e164='+919000000001'
)

# Add donor details
details = DonorDetails.objects.create(
    user=user,
    full_name='John Doe',
    age=25,
    blood_group='O+',
    city='Bangalore',
    is_available=True
)
```

## ✅ Step 4: Testing

### Option A: Run Test Script
```bash
python test_sos_sms_workflow.py
```

### Option B: Use Management Command
```bash
python manage.py test_sos_workflow --patient=1 --blood-group=O+ --city=Bangalore
```

### Option C: Manual API Testing
1. Create SOS request via API
2. Call `/api/sos/requests/{id}/match/` endpoint
3. Check if SMS is sent (check logs)

## ✅ Step 5: Verify SMS Sending

### Check Logs:
```bash
tail -f logs/django.log | grep SMS
```

### Check Database:
```bash
python manage.py shell
>>> from sos.models import SOSResponse
>>> SOSResponse.objects.filter(channel='sms').count()
```

### Check Provider Dashboard:
- Log into Fast2SMS/Textlocal account
- Check SMS delivery status
- Verify sender ID matches

## ✅ Step 6: Production Deployment

- [ ] Update .env with production SMS API key
- [ ] Set `DEBUG = False` in settings
- [ ] Enable HTTPS
- [ ] Set up SMS webhook endpoint (for SMS replies)
- [ ] Configure logging to file/external service
- [ ] Test SMS sending before going live
- [ ] Set up monitoring for SMS failures

## ⚠️ Troubleshooting Quick Fix

### SMS Not Sending?
1. Check if SMS_API_KEY is set: `echo $SMS_API_KEY`
2. Check donor has phone number: `Profile.objects.get(user__username='donor1').phone_e164`
3. Check city matches: `DonorDetails.objects.filter(city='Bangalore', is_available=True).count()`
4. Check logs: `python manage.py shell` and test `send_sms('+919000000001', 'test')`

### No Donors Found?
1. Verify donor city matches SOS city (case-sensitive)
2. Check donor blood group is compatible
3. Verify `is_available=True` for donors
4. Check if blood group compatibility is configured

### SMS Provider Error?
1. Verify API key is correct in provider dashboard
2. Check sender ID is configured correctly
3. Try test SMS directly from provider dashboard
4. Check phone number format (E.164: +country_code_number)

## 📞 SMS Reply Handling

When donors reply via SMS:
- System receives SMS via provider webhook
- Parses response: YES, NO, YES SHARE
- Updates SOSResponse record
- Notifies patient via email/app

### Configure Webhook (Optional):
```
Provider Dashboard > Webhooks/Callbacks
URL: https://yourapp.com/api/sos/inbound/
Method: POST
```

## 🎯 Success Criteria

- [ ] SMS API key configured and verified
- [ ] At least one donor has phone number in E.164 format
- [ ] Test script runs without errors
- [ ] SMS delivery shown in provider dashboard
- [ ] Database shows SOSResponse with channel='sms'
- [ ] Donors can create accounts and donate blood
- [ ] Patients can create SOS requests
- [ ] System finds matching donors
- [ ] SMS sent to matching donors

## 📚 Documentation

- Full setup guide: [SOS_SMS_SETUP_GUIDE.md](SOS_SMS_SETUP_GUIDE.md)
- API documentation: Check DRF Swagger endpoint
- Model documentation: Check model docstrings in `sos/models.py`

## 🚀 Next Steps

1. [ ] Run test script successfully
2. [ ] Configure webhook for SMS replies
3. [ ] Set up SMS rate limiting
4. [ ] Monitor SMS delivery metrics
5. [ ] Implement donor availability notifications
6. [ ] Add leaderboard/gamification
