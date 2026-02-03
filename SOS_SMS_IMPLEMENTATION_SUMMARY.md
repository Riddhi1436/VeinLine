# SOS SMS Workflow - Implementation Summary

## 🎯 Objective
Make the SOS feature work correctly so that when a patient sends an SOS, SMS notifications are sent to matching donors, creating a working connection between patients and donors.

## ✅ Changes Made

### 1. **Fixed SMS Service** (`core/services/sms.py`)
**What was improved:**
- Added comprehensive error handling
- Better exception handling for network issues
- Proper logging for debugging
- Graceful degradation when SMS_API_KEY is missing
- Returns detailed status information for each SMS attempt
- Validates phone number format before sending
- Handles multiple SMS providers (Fast2SMS, Textlocal)

**Key improvements:**
```python
- Added timeout handling
- Added request exception handling
- Added phone number validation
- Detailed error responses with reason codes
- Proper logging at INFO/ERROR levels
```

### 2. **Improved SOS Views** (`sos/views.py`)
**What was fixed:**
- Added proper logging import
- Improved match endpoint to send SMS to each donor individually
- Better error handling during SMS sending (try-catch per donor)
- Detailed SMS results reporting
- Atomic transactions for database consistency
- Each donor SMS failure doesn't block others
- Sends email fallback if SMS fails

**Key improvements:**
```python
- SMS sent inside atomic transaction
- Individual error handling per donor
- Detailed SMS results with phone numbers
- Proper response status codes
- Fallback email notification
```

### 3. **Created Management Command** (`sos/management/commands/test_sos_workflow.py`)
**Purpose:** Easy testing of SOS workflow from command line

**Usage:**
```bash
python manage.py test_sos_workflow \
  --patient=<patient_id> \
  --blood-group=O+ \
  --city=Bangalore \
  --priority=urgent \
  --units=2 \
  --hospital="Apollo Hospital" \
  --area="Indiranagar"
```

**Features:**
- Creates SOS request
- Finds matching donors automatically
- Sends SMS to all matching donors
- Shows success/failure statistics
- Color-coded output for clarity

### 4. **Created Test Script** (`test_sos_sms_workflow.py`)
**Purpose:** Complete end-to-end test of SOS SMS workflow

**What it does:**
1. Creates test patient user with profile
2. Creates 3 test donor users with phone numbers
3. Creates donor details for each donor
4. Creates SOS request
5. Matches donors automatically
6. Sends SMS to each donor
7. Reports success/failure statistics

**Run with:**
```bash
python test_sos_sms_workflow.py
```

### 5. **Documentation**
**Created comprehensive guides:**

#### a) `SOS_SMS_SETUP_GUIDE.md` - Complete Setup Guide
- Configuration steps
- SMS provider setup (Fast2SMS, Textlocal)
- Data model explanation
- Workflow explanation
- Testing methods (3 options)
- Troubleshooting guide
- API endpoints
- Performance considerations
- Security considerations

#### b) `SOS_SMS_QUICK_SETUP.md` - Quick Checklist
- Step-by-step setup checklist
- Quick troubleshooting
- Success criteria
- Next steps

## 🔧 Model Structure

### Patient → SOS Request Flow
```
Patient (User)
  └─ Profile (email, phone_e164)
     └─ Patient role
        └─ Creates SOSRequest
           ├─ blood_group_needed
           ├─ city
           ├─ sms_reply_token (auto-generated)
           └─ Creates multiple SOSResponse
              └─ One per matching donor
```

### Donor → Response Flow
```
Donor (User)
  ├─ Profile (phone_e164 in E.164 format: +919000000001)
  ├─ role = 'donor'
  ├─ DonorDetails
  │  ├─ full_name
  │  ├─ blood_group
  │  ├─ city (must match SOS city for matching)
  │  ├─ is_available = True
  │  └─ Receives SMS
  └─ SOSResponse (created when matched)
     ├─ request = SOSRequest
     ├─ response (yes/no/pending)
     ├─ channel = 'sms'
     └─ donor_consented_to_share_contact (privacy)
```

## 📊 Database Models Updated

### SOSRequest
- Stores SOS information
- `sms_reply_token`: Auto-generated for SMS replies
- Indexes on (status, blood_group, city), (created_at), (priority, status)

### SOSResponse
- Links donor to SOS request
- Tracks response (yes/no/pending)
- Tracks channel (web/sms)
- Unique constraint on (request, donor)
- Indexes on (request, response), (donor, response)

### DonorDetails
- Donor profile with blood group and location
- `is_available`: Controls matching
- Indexes on (blood_group, city, is_available)

### Profile (accounts/models.py)
- `phone_e164`: Phone number in E.164 format
- Must be set for SMS to work
- Format: +<country_code><number> (e.g., +919000000001)

## 🔌 API Endpoints Involved

```
POST /api/sos/requests/          - Create SOS request
GET  /api/sos/requests/          - List SOS requests
GET  /api/sos/requests/{id}/     - Get SOS details
POST /api/sos/requests/{id}/match/ - MATCH AND SEND SMS TO DONORS
GET  /api/sos/responses/         - List all responses
GET  /api/sos/responses/{id}/    - Get response details
POST /api/sos/responses/{id}/respond/ - Donor responds
POST /api/sos/inbound/           - SMS webhook (provider callback)
```

## 🚀 Configuration Required

### 1. Environment Variables (.env)
```env
SMS_PROVIDER=fast2sms
SMS_API_KEY=your_actual_api_key_here
SMS_SENDER=VEINLN
```

### 2. SMS Provider
- **Fast2SMS**: https://www.fast2sms.com (India)
- **Textlocal**: https://www.textlocal.in (Global)

### 3. Donor Phone Numbers
- Must be in E.164 format: +<country_code><number>
- Example: +919876543210 (India)

## ✨ Key Features Implemented

### Patient Side
- Create SOS request with blood group, units, location, priority
- Automatic donor matching
- SMS notification to donors
- Track donor responses
- Reveal contact info (with privacy control)

### Donor Side
- Receive SMS alert for matching SOS
- Respond YES/NO/YES+SHARE via SMS or web
- Track SOS responses
- Earn badges for SOS participation

### System
- Blood group compatibility matching
- Geographic matching (city-based)
- Automatic sms_reply_token generation
- Privacy-first approach (contact only revealed with consent)
- Email fallback if SMS fails
- Comprehensive error handling
- Detailed logging

## 🧪 Testing Workflow

### Quick Test (5 minutes):
```bash
python test_sos_sms_workflow.py
```

### Detailed Test (with options):
```bash
python manage.py test_sos_workflow --patient=1 --blood-group=O+ --city=Bangalore
```

### Manual Test (via API):
1. Login as patient
2. Create SOS request: `POST /api/sos/requests/`
3. Trigger matching: `POST /api/sos/requests/{id}/match/`
4. Check responses: `GET /api/sos/responses/`

## 🐛 Debugging Tips

### Check SMS Configuration
```bash
python manage.py shell
>>> from django.conf import settings
>>> print(settings.VEINLINE_SMS_API_KEY)  # Should not be empty
>>> print(settings.VEINLINE_SMS_PROVIDER)  # Should be fast2sms or textlocal
```

### Check Donor Phone Numbers
```bash
>>> from accounts.models import Profile
>>> Profile.objects.filter(phone_e164__isnull=False).values_list('user__username', 'phone_e164')
```

### Test SMS Sending
```bash
>>> from core.services.sms import send_sms
>>> result = send_sms('+919876543210', 'Test message')
>>> print(result)
```

### Check SOS Records
```bash
>>> from sos.models import SOSRequest, SOSResponse
>>> SOSRequest.objects.all()  # List all SOS requests
>>> SOSResponse.objects.filter(channel='sms')  # SMS responses only
```

## 📈 Production Deployment

1. Configure SMS_API_KEY in production environment
2. Ensure all donors have phone_e164 set
3. Test SMS sending before going live
4. Monitor SMS delivery metrics
5. Set up error alerts for SMS failures
6. Configure webhook endpoint for SMS replies
7. Enable rate limiting if needed

## 🔐 Security Measures

- Phone numbers not exposed without donor consent
- Token-based SMS replies (no passwords sent)
- SMS token rotation capability
- Privacy settings per SOS request
- Secure E.164 phone format validation

## 📝 Files Modified/Created

### Modified Files:
- `core/services/sms.py` - Enhanced error handling
- `sos/views.py` - Improved SMS sending in match endpoint

### New Files:
- `sos/management/__init__.py`
- `sos/management/commands/__init__.py`
- `sos/management/commands/test_sos_workflow.py` - Management command
- `test_sos_sms_workflow.py` - End-to-end test script
- `SOS_SMS_SETUP_GUIDE.md` - Comprehensive setup documentation
- `SOS_SMS_QUICK_SETUP.md` - Quick setup checklist
- `SOS_SMS_IMPLEMENTATION_SUMMARY.md` - This file

## ✅ Testing Checklist

- [ ] SMS_API_KEY configured in .env
- [ ] Test patient user created
- [ ] Test donor users created with phone numbers
- [ ] DonorDetails created for donors
- [ ] SOS request created
- [ ] Donors matched successfully
- [ ] SMS sent without errors
- [ ] SOSResponse records created
- [ ] Can view SOS responses via API
- [ ] Error handling works (missing phone, etc.)

## 🎉 Success Indicators

✅ When you see these, SOS SMS is working:

1. **Test script runs successfully**
   ```
   ✓ SOS Request created: #1
   ✓ Found 3 matching donors
   ✓ SMS sent successfully: 3/3
   ```

2. **Management command works**
   ```
   ✓ SOS request created: #1
   ✓ Found 5 matching donors
   Matched Donors Found: 5
   SMS Statistics:
     ✓ Sent: 5
   ```

3. **API endpoint returns success**
   ```json
   {
     "request_id": 1,
     "matched_donors": 5,
     "sms_results": [
       {"donor_id": 2, "sms": {"ok": true}}
     ]
   }
   ```

4. **SMS appears in provider dashboard**
   - Check Fast2SMS or Textlocal dashboard
   - Verify SMS delivery status
   - Check sender ID matches

## 🚀 Next Steps

1. Set SMS_API_KEY in .env file
2. Run test script: `python test_sos_sms_workflow.py`
3. Configure webhook for SMS replies (optional)
4. Deploy to production
5. Monitor SMS delivery metrics
6. Set up donor notifications/gamification

---

**Status**: ✅ Complete and Ready for Testing

**Last Updated**: 2024-01-31
