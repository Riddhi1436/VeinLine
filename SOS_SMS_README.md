# 🩸 VeinLine SOS SMS Feature - Complete Guide

Welcome! This guide helps you understand and use the SOS SMS feature that enables patients to send emergency blood requests to donors via SMS.

## 📋 Quick Start (Choose Your Path)

### 🏃 I Want to Test It Right Now (5 minutes)
1. Set API key: `export SMS_API_KEY=your_key`
2. Run test: `python test_sos_sms_workflow.py`
3. See results

👉 **Go to**: [SOS_SMS_QUICK_REFERENCE.md](SOS_SMS_QUICK_REFERENCE.md)

### 📖 I Want to Understand Everything (30 minutes)
Read the complete setup and architecture guide

👉 **Go to**: [SOS_SMS_SETUP_GUIDE.md](SOS_SMS_SETUP_GUIDE.md)

### ✅ I Want Step-by-Step Instructions (15 minutes)
Follow the detailed setup checklist

👉 **Go to**: [SOS_SMS_QUICK_SETUP.md](SOS_SMS_QUICK_SETUP.md)

### 🐛 Something Isn't Working (Find Your Issue)
Use the troubleshooting flowchart to debug

👉 **Go to**: [SOS_SMS_TROUBLESHOOTING.md](SOS_SMS_TROUBLESHOOTING.md)

### 🔧 I Want Technical Details
See what was implemented and how

👉 **Go to**: [SOS_SMS_IMPLEMENTATION_SUMMARY.md](SOS_SMS_IMPLEMENTATION_SUMMARY.md)

## 🎯 What Is This Feature?

**Problem**: Patients in emergency need blood, but don't know which donors can help.

**Solution**: When a patient creates an SOS request, the system automatically:
1. Finds compatible donors in the same city
2. Sends SMS alerts to those donors
3. Donors respond YES/NO via SMS or web
4. Patient gets the list of willing donors

## 📊 How It Works

```
Patient Creates SOS
      ↓
System Finds Matching Donors
      ↓
SMS Sent to Each Donor
      ↓
Donor Receives: "Need O+ blood in Bangalore"
      ↓
Donor Replies: "YES <token>" or "NO <token>"
      ↓
Patient Sees: "5 donors said YES"
      ↓
Patient Can Call/Message Donors
```

## 🔧 Core Components

### Models
- **SOSRequest**: Emergency blood request from patient
- **SOSResponse**: Donor's response to SOS
- **DonorDetails**: Donor information (blood group, city, availability)
- **Profile**: User profile with phone number

### Services
- **SMS Service** (`core/services/sms.py`): Sends SMS via Fast2SMS/Textlocal
- **Matching Service** (`sos/services.py`): Finds compatible donors

### API Endpoints
- `POST /api/sos/requests/` - Create SOS
- `POST /api/sos/requests/{id}/match/` - Match and send SMS
- `GET /api/sos/responses/` - View responses

### Management Command
- `python manage.py test_sos_workflow` - Test workflow from CLI

## 📱 SMS Requirements

### For the System
- SMS Provider API Key (Fast2SMS or Textlocal)
- API key stored in environment variable: `SMS_API_KEY`
- Provider configured: `SMS_PROVIDER=fast2sms` or `textlocal`

### For Donors
- Phone number in E.164 format: `+919876543210`
- City same as SOS city (exact match, case-sensitive)
- Status: Available for donation (`is_available=True`)
- Blood group: Compatible with needed blood group

### For Patients
- Valid user account with "patient" role
- Can create SOS requests with blood group, location, priority

## 🚀 Getting Started

### Step 1: Configure SMS Provider

Choose one:
- **Fast2SMS** (India): https://www.fast2sms.com
- **Textlocal** (Global): https://www.textlocal.in

Get API key from dashboard

### Step 2: Set Environment Variable

```bash
export SMS_API_KEY=your_api_key_here
export SMS_PROVIDER=fast2sms
```

### Step 3: Create Test Data

```bash
python test_sos_sms_workflow.py
```

This automatically:
- Creates test patient
- Creates test donors with phone numbers
- Creates SOS request
- Tests SMS sending

### Step 4: Verify Success

Look for output:
```
✓ SOS Request created: #1
✓ Found 3 matching donors
✓ SMS Sent: 3/3
```

## 📚 Documentation Map

| Document | Purpose | When to Read |
|----------|---------|--------------|
| [SOS_SMS_QUICK_REFERENCE.md](SOS_SMS_QUICK_REFERENCE.md) | Quick answers and code snippets | Need quick answer |
| [SOS_SMS_SETUP_GUIDE.md](SOS_SMS_SETUP_GUIDE.md) | Comprehensive technical guide | Learning system in depth |
| [SOS_SMS_QUICK_SETUP.md](SOS_SMS_QUICK_SETUP.md) | Step-by-step checklist | Following setup process |
| [SOS_SMS_TROUBLESHOOTING.md](SOS_SMS_TROUBLESHOOTING.md) | Flowchart for debugging | Something isn't working |
| [SOS_SMS_IMPLEMENTATION_SUMMARY.md](SOS_SMS_IMPLEMENTATION_SUMMARY.md) | Technical details of changes | Interested in code changes |
| README.md (this file) | Overview and navigation | Getting oriented |

## ✨ Key Features

### ✅ For Patients
- Create emergency blood requests
- Specify blood group, location, priority
- See donor responses immediately
- Contact donors privately (with consent)
- Track SOS status

### ✅ For Donors
- Receive SMS for matching emergencies
- Quick response via SMS or web
- Control contact sharing (privacy)
- Earn badges for helping
- No direct phone number exposure

### ✅ For System
- Automatic donor matching (blood group + location)
- SMS notifications with token-based replies
- Privacy-first (contact only revealed with consent)
- Error handling and email fallback
- Comprehensive logging

## 🔐 Security & Privacy

- **Phone numbers** are never shared without explicit consent
- **SMS replies** use tokens, not passwords
- **Token rotation** available if abuse detected
- **E.164 validation** ensures phone format
- **Role-based access** controls who can do what

## 📊 Database Schema

```
User (Django's built-in)
├── Profile
│   ├── role (patient/donor)
│   ├── phone_e164 (+919876543210)
│   └── city
├── DonorDetails (if donor)
│   ├── full_name
│   ├── blood_group (O+, A-, etc.)
│   ├── city
│   ├── is_available (True/False)
│   └── last_donated_at
└── SOSRequest (if created SOS)
    ├── blood_group_needed
    ├── units_needed
    ├── city
    ├── priority (normal/urgent/critical)
    ├── status (open/fulfilled/cancelled)
    ├── sms_reply_token (auto-generated)
    └── SOSResponse (one per donor)
        ├── response (yes/no/pending)
        ├── channel (web/sms)
        └── donor_consented_to_share_contact
```

## 🧪 Testing

### Quick Test (Automated)
```bash
python test_sos_sms_workflow.py
```

### Manual Test (CLI)
```bash
python manage.py test_sos_workflow --patient=1 --blood-group=O+ --city=Bangalore
```

### API Test (Manual)
```bash
# Create SOS
curl -X POST http://localhost:8000/api/sos/requests/ \
  -H "Authorization: Bearer <token>" \
  -d '{"blood_group_needed":"O+","city":"Bangalore"}'

# Match and send SMS
curl -X POST http://localhost:8000/api/sos/requests/1/match/ \
  -H "Authorization: Bearer <token>"
```

## 🐛 Common Issues

| Issue | Solution |
|-------|----------|
| SMS not sending | Ensure `SMS_API_KEY` is set |
| No donors found | Check city name matches exactly |
| Wrong phone format | Use E.164: +919876543210 |
| API auth failed | Get JWT token from login endpoint |

**For detailed troubleshooting**: See [SOS_SMS_TROUBLESHOOTING.md](SOS_SMS_TROUBLESHOOTING.md)

## 🚀 What's New

### Fixed/Enhanced
- ✅ SMS service with comprehensive error handling
- ✅ Match endpoint properly sends SMS to each donor
- ✅ Better logging for debugging
- ✅ Atomic transactions for consistency
- ✅ Email fallback if SMS fails

### Added
- ✅ Management command for testing
- ✅ End-to-end test script
- ✅ Comprehensive documentation
- ✅ Troubleshooting guide
- ✅ Quick reference guide

## 📞 Support

**If you're stuck:**

1. Check [SOS_SMS_TROUBLESHOOTING.md](SOS_SMS_TROUBLESHOOTING.md)
2. Run: `python test_sos_sms_workflow.py` (for diagnosis)
3. Check Django logs for errors
4. Verify SMS provider account is active
5. Ensure all required fields are set

## 📈 Production Deployment

Before going live:

- [ ] Set `DEBUG = False`
- [ ] Configure production SMS API key
- [ ] Test SMS sending with real phone numbers
- [ ] Set up error alerts for SMS failures
- [ ] Configure webhook for SMS replies (optional)
- [ ] Monitor SMS delivery metrics
- [ ] Set up backup SMS provider if needed

## 🎯 Next Steps

1. **Quick start**: Run `python test_sos_sms_workflow.py`
2. **Learn more**: Read [SOS_SMS_SETUP_GUIDE.md](SOS_SMS_SETUP_GUIDE.md)
3. **Get help**: Use [SOS_SMS_TROUBLESHOOTING.md](SOS_SMS_TROUBLESHOOTING.md) if needed
4. **Deploy**: Follow production checklist above

## ✅ Success Indicators

You know it's working when:

```
✓ test_sos_sms_workflow.py shows "SMS Sent: N/N"
✓ SMS appears in provider dashboard
✓ Donors receive SMS on their phones
✓ Database shows SOSResponse with channel='sms'
✓ Donors can reply YES/NO via SMS
```

## 📄 Files Reference

### Core Implementation
- `sos/models.py` - SOSRequest, SOSResponse models
- `sos/views.py` - API endpoints for SOS
- `sos/services.py` - Donor matching logic
- `sos/serializers.py` - Data serialization
- `core/services/sms.py` - SMS sending service

### New Files
- `test_sos_sms_workflow.py` - End-to-end test script
- `sos/management/commands/test_sos_workflow.py` - Management command
- Documentation files (this README + 4 guide files)

### Related Models
- `accounts/models.py` - User Profile
- `donations/models.py` - DonorDetails

## 🎓 Learning Path

**Beginner** (15 min):
1. Read this README
2. Run `python test_sos_sms_workflow.py`
3. Check results

**Intermediate** (45 min):
1. Read [SOS_SMS_QUICK_SETUP.md](SOS_SMS_QUICK_SETUP.md)
2. Follow setup steps
3. Test manually

**Advanced** (2 hours):
1. Read [SOS_SMS_SETUP_GUIDE.md](SOS_SMS_SETUP_GUIDE.md)
2. Read [SOS_SMS_IMPLEMENTATION_SUMMARY.md](SOS_SMS_IMPLEMENTATION_SUMMARY.md)
3. Explore code in `sos/` app
4. Customize for your needs

---

## 🎉 Ready to Get Started?

**Choose one:**
- **Just want to test?** → Run: `python test_sos_sms_workflow.py`
- **Want step-by-step?** → Open: [SOS_SMS_QUICK_SETUP.md](SOS_SMS_QUICK_SETUP.md)
- **Want full details?** → Open: [SOS_SMS_SETUP_GUIDE.md](SOS_SMS_SETUP_GUIDE.md)
- **Something broken?** → Open: [SOS_SMS_TROUBLESHOOTING.md](SOS_SMS_TROUBLESHOOTING.md)

**Questions?** Check the relevant guide file above!
