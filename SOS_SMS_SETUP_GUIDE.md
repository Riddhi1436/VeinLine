# SOS SMS Workflow Setup Guide

## Overview
The SOS SMS feature enables patients to send emergency blood requests to donors via SMS notifications. When a patient creates an SOS request, matching donors receive SMS alerts and can respond via SMS.

## Configuration

### 1. Environment Variables (.env)

Add these variables to your `.env` file:

```env
# SMS Provider Configuration
SMS_PROVIDER=fast2sms              # Options: fast2sms, textlocal
SMS_API_KEY=your_api_key_here      # Get from provider
SMS_SENDER=VEINLN                  # Sender ID (max 6 chars for most providers)
```

### 2. Supported SMS Providers

#### Fast2SMS
- **Website**: https://www.fast2sms.com
- **API Endpoint**: https://www.fast2sms.com/dev/bulkV2
- **Setup**: 
  1. Sign up and get API key
  2. Set `SMS_PROVIDER=fast2sms` and `SMS_API_KEY=your_key`

#### Textlocal
- **Website**: https://www.textlocal.in
- **API Endpoint**: https://api.textlocal.in/send/
- **Setup**:
  1. Sign up and get API key
  2. Set `SMS_PROVIDER=textlocal` and `SMS_API_KEY=your_key`

## Data Model

### SOSRequest
- `requester`: Patient user who needs blood
- `blood_group_needed`: Blood group required
- `units_needed`: Number of units
- `city`: City where blood is needed
- `area`: Area/locality
- `hospital_name`: Hospital name
- `message`: Additional message
- `status`: open, fulfilled, cancelled
- `priority`: normal, urgent, critical
- `sms_reply_token`: Token for SMS replies (auto-generated)

### SOSResponse
- `request`: Foreign key to SOSRequest
- `donor`: Foreign key to User (donor)
- `response`: yes, no, pending
- `channel`: web, sms
- `donor_consented_to_share_contact`: Privacy flag
- `patient_contact_revealed_at`: When contact was revealed

### DonorDetails
- `user`: Foreign key to User
- `full_name`: Donor's name
- `blood_group`: Blood group
- `city`: City
- `is_available`: Availability status
- Profile must have `phone_e164` in E.164 format (+country code...)

## Workflow

### 1. Creating an SOS Request

**Via API (POST /api/sos/requests/)**
```json
{
  "blood_group_needed": "O+",
  "units_needed": 2,
  "city": "Bangalore",
  "area": "Indiranagar",
  "hospital_name": "Apollo Hospital",
  "message": "Emergency surgery",
  "priority": "urgent"
}
```

**Via Django Admin**
- Go to Admin > SOS > SOS Requests
- Click "Add SOS Request"
- Fill in details and save

### 2. Matching and Notifying Donors

**Via API (POST /api/sos/requests/{id}/match/)**
- Triggers the matching algorithm
- Finds donors with:
  - Compatible blood group
  - Same city (configurable)
  - Available status = True
- Creates SOSResponse records
- Sends SMS to each matching donor's phone_e164

**Response:**
```json
{
  "request_id": 1,
  "matched_donors": 5,
  "responses_created_or_found": [
    {"donor_id": 2, "created": true, "response_id": 1}
  ],
  "sms_results": [
    {
      "donor_id": 2,
      "donor_name": "John Doe",
      "phone": "+919000000001",
      "sms": {"ok": true, "provider": "fast2sms"}
    }
  ]
}
```

### 3. SMS Format

Donors receive SMS like:
```
VeinLine SOS: Need O+ blood in Bangalore. Reply: YES <token> or NO <token>. (Optional consent: YES SHARE <token>)
```

### 4. Donor Response via SMS

Donors can reply:
- `YES <token>` - Accept to donate
- `NO <token>` - Cannot donate
- `YES SHARE <token>` - Accept AND consent to share contact

### 5. Checking Responses

**Via API (GET /api/sos/responses/)**
```json
{
  "id": 1,
  "request": 1,
  "donor": 2,
  "donor_name": "John Doe",
  "donor_blood_group": "O+",
  "response": "yes",
  "channel": "sms",
  "responded_at": "2024-01-31T10:30:00Z"
}
```

## Testing

### Option 1: Management Command

```bash
python manage.py test_sos_workflow \
  --patient=<patient_id> \
  --blood-group=O+ \
  --city=Bangalore \
  --priority=urgent \
  --units=2
```

Example:
```bash
python manage.py test_sos_workflow --patient=1 --blood-group=O+ --city=Bangalore
```

### Option 2: Test Script

```bash
python test_sos_sms_workflow.py
```

This script:
1. Creates test patient and donor users
2. Adds donor details with phone numbers
3. Creates an SOS request
4. Matches donors
5. Tests SMS sending
6. Prints detailed results

### Option 3: Manual Testing via API

1. **Create patient (if needed)**
```bash
curl -X POST http://localhost:8000/api/accounts/users/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "patient1",
    "email": "patient@test.com",
    "password": "testpass123",
    "profile": {"role": "patient", "city": "Bangalore"}
  }'
```

2. **Create SOS request**
```bash
curl -X POST http://localhost:8000/api/sos/requests/ \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "blood_group_needed": "O+",
    "units_needed": 2,
    "city": "Bangalore",
    "priority": "urgent"
  }'
```

3. **Match and notify donors**
```bash
curl -X POST http://localhost:8000/api/sos/requests/1/match/ \
  -H "Authorization: Bearer <token>"
```

## Troubleshooting

### SMS Not Sending

1. **Check API Key**: Verify `SMS_API_KEY` is set in `.env`
```bash
python manage.py shell
>>> from django.conf import settings
>>> settings.VEINLINE_SMS_API_KEY  # Should not be empty
```

2. **Check Provider**: Verify provider is set correctly
```bash
>>> settings.VEINLINE_SMS_PROVIDER  # Should be 'fast2sms' or 'textlocal'
```

3. **Check Phone Numbers**: Ensure donors have phone numbers in E.164 format
```bash
>>> from accounts.models import Profile
>>> Profile.objects.filter(role='donor').values_list('phone_e164')
```

4. **Check Logs**: Enable logging to see SMS errors
```python
# In settings.py
LOGGING = {
    'version': 1,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'core.services.sms': {
            'handlers': ['console'],
            'level': 'DEBUG',
        },
    },
}
```

### No Matching Donors

1. **Verify city matching**: Is city case-sensitive?
```python
# Check settings
>>> from django.conf import settings
>>> settings.VEINLINE_CITY_MATCH_STRICT  # True = strict, False = flexible
```

2. **Check donor availability**
```bash
python manage.py shell
>>> from donations.models import DonorDetails
>>> DonorDetails.objects.filter(is_available=True, city='Bangalore')
```

3. **Check blood group compatibility**
```bash
>>> from sos.services import compatible_donor_groups
>>> compatible_donor_groups('O+')  # Should return compatible groups
```

## Advanced Configuration

### City Matching (Flexible)

By default, city matching is strict (exact match). To allow flexibility:

```python
# settings.py
VEINLINE_CITY_MATCH_STRICT = False  # Allow blank city for rural/offline data
```

### Blood Bank Integration

The system can also consider blood bank inventory:

```bash
python manage.py shell
>>> from donations.models import BloodBankInventory
>>> BloodBankInventory.objects.create(
...     city='Bangalore',
...     blood_group='O+',
...     units_available=10
... )
```

## API Endpoints

- `POST /api/sos/requests/` - Create SOS request
- `GET /api/sos/requests/` - List SOS requests
- `GET /api/sos/requests/{id}/` - Get SOS request details
- `POST /api/sos/requests/{id}/match/` - Match donors and send SMS
- `GET /api/sos/responses/` - List SOS responses
- `GET /api/sos/responses/{id}/` - Get response details
- `POST /api/sos/responses/{id}/respond/` - Donor responds
- `POST /api/sos/responses/{id}/reveal_contact/` - Reveal patient contact
- `POST /api/sos/inbound/` - SMS webhook endpoint

## Performance Considerations

1. **Large Donor Lists**: The match endpoint iterates through all matching donors
   - Limit: Currently limited to 50 donors per request
   - For many donors, consider using background tasks (Celery)

2. **SMS Timeout**: Each SMS has a 20-second timeout
   - Configure SMS provider for reliability
   - Consider async sending for better UX

3. **Database Queries**: Uses select_related for optimization
   - DonorDetails and User relationship is optimized
   - SOSResponse queries use proper indexing

## Security Considerations

1. **Phone Privacy**: Phone numbers are not exposed unless donor consents
2. **Token-based SMS Reply**: SMS replies use tokens, not passwords
3. **SMS Token Rotation**: Tokens are rotated if abused
4. **Rate Limiting**: Consider rate limiting on SMS endpoints

## Next Steps

1. Configure SMS provider API key in .env
2. Ensure all donors have phone numbers in E.164 format
3. Test with test_sos_sms_workflow.py
4. Monitor SMS sending in production logs
5. Set up monitoring alerts for SMS failures
