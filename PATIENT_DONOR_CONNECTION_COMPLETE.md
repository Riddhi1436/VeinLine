# Patient SOS Request to Donor Response Connection - Complete Setup

## Overview

The VeinLine platform now has a fully functional connection between **patient SOS blood requests** and **donor responses**. This document details the complete architecture and how the system works.

---

## Database Schema

### Key Models and Relationships

```
Patient (User)
    ↓ creates
SOSRequest
    ├─ requester (ForeignKey to User/Patient)
    ├─ blood_group_needed
    ├─ units_needed
    ├─ city, area
    ├─ priority (NORMAL, URGENT, CRITICAL)
    ├─ status (OPEN, FULFILLED, CANCELLED)
    └─ sms_reply_token (for SMS responses)
    
    ↓ generates multiple
SOSResponse
    ├─ request (ForeignKey to SOSRequest)
    ├─ donor (ForeignKey to User/Donor)
    ├─ response (PENDING, YES, NO)
    ├─ channel (WEB, SMS)
    ├─ donor_consented_to_share_contact (Boolean)
    ├─ patient_contact_revealed_at (DateTime)
    ├─ responded_at (DateTime)
    └─ unique_together: (request, donor)
    
    ↓ creates (if YES)
DonationTracker
    ├─ sos_response (OneToOneField)
    ├─ current_status (AGREED, TRAVELING, ARRIVED, DONATING, COMPLETED, CANCELLED)
    ├─ current_latitude, current_longitude (Location tracking)
    ├─ estimated_arrival_time
    ├─ Status timestamps (agreed_at, traveling_at, arrived_at, donating_at, completed_at)
    └─ notes
```

---

## Complete Flow

### 1. Patient Creates SOS Request

```python
# POST /api/sos/requests/
{
    "blood_group_needed": "O+",
    "units_needed": 2,
    "city": "DELHI",
    "area": "Central Delhi",
    "hospital_name": "Delhi Medical Center",
    "message": "Urgent blood needed",
    "priority": "urgent"
}
```

**Backend Process:**
- `SOSRequestViewSet.perform_create()` saves with `requester=current_user`
- `sms_reply_token` auto-generated (32-char hex)
- Status set to `OPEN`

---

### 2. Patient Matches Donors

```python
# POST /api/sos/requests/{id}/match/
```

**What Happens:**
1. `match_donors_for_request()` finds compatible donors:
   - Blood group compatibility
   - Same city
   - Is available
   - Limits to 50 donors
   
2. For each matched donor:
   - Create `SOSResponse` (status: PENDING, channel: SMS)
   - Send SMS alert with `sms_reply_token` for reply
   - Send email fallback
   - Log all results

**SMS Message Template:**
```
VeinLine SOS: Need O+ blood in DELHI. 
Reply: YES {token} or NO {token}.
(Optional consent: YES SHARE {token})
```

---

### 3. Donor Responds

#### Option A: Via Web UI
```python
# POST /api/sos/responses/{id}/respond/
{
    "response": "yes",      # or "no"
    "consent_to_share_contact": true
}
```

#### Option B: Via SMS
```
Webhook POST to /api/sms/inbound/
{
    "from_phone": "+919876543210",
    "message": "YES SHARE {token}"
}
```

**Response Parsing:**
- `YES {token}` → Agrees to donate
- `NO {token}` → Declines
- `YES SHARE {token}` → Agrees + Consents to share contact

**Backend Process:**
1. Update `SOSResponse`:
   - `response` = YES/NO
   - `responded_at` = now
   - `donor_consented_to_share_contact` = true (if consented)
   - `channel` = WEB/SMS

2. If `response == YES`:
   - Create `DonationTracker` (status: AGREED)
   - Send notification to patient

3. Notify patient of response

---

### 4. Donation Tracking (If YES)

```python
# POST /api/sos/tracker/{id}/update_status/
{
    "status": "traveling",
    "latitude": 28.7041,
    "longitude": 77.1025
}
```

**Status Flow:**
```
AGREED → TRAVELING → ARRIVED → DONATING → COMPLETED (or CANCELLED)
```

Each status update:
- Timestamps the transition
- Updates location (if provided)
- Notifies patient

---

### 5. Patient Reveals Contact (If Donor Consented)

```python
# POST /api/sos/responses/{id}/reveal_contact/
```

**Privacy Rule:**
- Contact only revealed if `donor_consented_to_share_contact == True`
- Sets `patient_contact_revealed_at` timestamp
- Returns donor phone in response serializer

---

## API Endpoints

### SOS Request Endpoints

| Method | Endpoint | Purpose | Auth |
|--------|----------|---------|------|
| GET | `/api/sos/requests/` | List user's requests (patient) or open requests (donor) | Required |
| POST | `/api/sos/requests/` | Create new SOS request | Patient only |
| GET | `/api/sos/requests/{id}/` | Get request details | Required |
| POST | `/api/sos/requests/{id}/match/` | Match donors and send alerts | Patient only |

### SOS Response Endpoints

| Method | Endpoint | Purpose | Auth |
|--------|----------|---------|------|
| GET | `/api/sos/responses/` | List responses (filtered by role) | Required |
| POST | `/api/sos/responses/{id}/respond/` | Donor responds to request | Donor only |
| POST | `/api/sos/responses/{id}/reveal_contact/` | Patient reveals donor contact | Patient only |

### Donation Tracker Endpoints

| Method | Endpoint | Purpose | Auth |
|--------|----------|---------|------|
| GET | `/api/sos/tracker/` | List user's trackers | Required |
| POST | `/api/sos/tracker/{id}/update_status/` | Update donation status | Donor only |

### SMS Endpoints

| Method | Endpoint | Purpose | Auth |
|--------|----------|---------|------|
| POST | `/api/sms/inbound/` | Receive SMS replies | None (webhook) |

---

## Permission Model

### Patient Permissions
- ✅ Create SOS requests
- ✅ View own SOS requests
- ✅ Trigger donor matching
- ✅ View responses to own requests
- ✅ Reveal donor contact (if consented)
- ❌ Cannot view other patients' requests
- ❌ Cannot respond to SOS requests

### Donor Permissions
- ✅ View open SOS requests in their city
- ✅ View/respond to SOS responses
- ✅ Update donation tracking status
- ✅ Optionally consent to share contact
- ❌ Cannot create SOS requests
- ❌ Cannot view other donors' responses

### Admin Permissions
- ✅ View all requests and responses
- ✅ View all donation trackers
- ✅ All patient and donor actions

---

## Privacy & Security

### Contact Visibility Rules

1. **Default (Hidden)**
   - Donor phone stored in `Profile.phone_e164` (E.164 format)
   - Never exposed in any list response
   - `SOSResponseSerializer.get_donor_phone()` returns `None`

2. **Donor Consent Required**
   - Donor must explicitly consent when responding
   - `SOSResponse.donor_consented_to_share_contact = True`
   - Sets via `/respond/` endpoint or SMS "YES SHARE" command

3. **Patient Request Required**
   - Even if donor consented, patient must call `/reveal_contact/`
   - Sets `patient_contact_revealed_at` timestamp
   - Only then is phone visible in response

### Multi-Layer Privacy Flow

```
Request Created
    ↓
Donors Matched → SOSResponse created (no contact shared)
    ↓
Donor Responds
    ├─ If "NO" → No contact ever shared
    ├─ If "YES" → Contact still hidden unless donor consented
    └─ If "YES SHARE" → Consent stored, but patient must reveal
    ↓
Patient Calls reveal_contact
    └─ Contact only visible if donor_consented_to_share_contact == True
```

---

## Data Flow Diagram

```
Patient Portal
    │
    ├─ Create SOS Request (#1)
    │       │
    │       ├─ blood_group_needed: O+
    │       ├─ city: DELHI
    │       └─ priority: URGENT
    │
    └─ Click "Match Donors"
            │
            ├─ Query: DonorDetails (O+, DELHI, is_available=True)
            │
            ├─ For each matching donor:
            │    │
            │    ├─ Create SOSResponse (PENDING)
            │    ├─ Send SMS alert
            │    └─ Store in DB
            │
            └─ Show matched donors (names only, no contact)

Donor Receives SMS
    │
    ├─ Reply: "YES SHARE {token}"
    │
    └─ Backend processes:
        │
        ├─ Parse SMS → token lookup → find SOSRequest
        ├─ Find User by phone
        ├─ Update SOSResponse:
        │    ├─ response = YES
        │    ├─ channel = SMS
        │    ├─ donor_consented_to_share_contact = True
        │    └─ responded_at = now()
        │
        └─ Create DonationTracker (AGREED)

Patient Views Responses
    │
    ├─ GET /api/sos/responses/ (filtered by request)
    │
    ├─ See donor list with status
    │ (contact hidden except for consented donors)
    │
    └─ For consented donors:
        │
        ├─ POST /reveal_contact/{id}
        │
        └─ Now can see phone number

Real-Time Tracking
    │
    └─ Donor updates status:
        │
        ├─ TRAVELING (with GPS)
        ├─ ARRIVED
        ├─ DONATING
        └─ COMPLETED
        │
        └─ Each status notifies patient
```

---

## Query Examples

### Patient Views Their SOS Requests

```python
# All requests created by this patient
SOSRequest.objects.filter(requester=patient_user)
```

### Patient Views Responses to Their Request

```python
# All donors who responded to this patient's SOS
SOSResponse.objects.filter(request__requester=patient_user)

# Only donors who said YES
SOSResponse.objects.filter(
    request__requester=patient_user,
    response='yes'
)

# Only donors who consented to share contact
SOSResponse.objects.filter(
    request__requester=patient_user,
    donor_consented_to_share_contact=True
)
```

### Donor Views Their Responses

```python
# All responses this donor has given
SOSResponse.objects.filter(donor=donor_user)

# SOS requests from their city
SOSRequest.objects.filter(
    status='open',
    city__iexact=donor_user.donor_details.city
)
```

### Find Active Donation Trackers

```python
# For a specific SOS request
DonationTracker.objects.filter(
    sos_response__request=sos_request
)

# For a donor
DonationTracker.objects.filter(
    sos_response__donor=donor_user
)

# Currently traveling
DonationTracker.objects.filter(
    current_status='traveling'
)
```

---

## Testing

### Setup Test Data

```bash
python setup_sos_connection.py
```

Creates:
- 3 test donors with details
- Patient with SOS request
- 3 SOSResponses (1 YES+CONSENT, 1 YES, 1 NO)
- 2 DonationTrackers

### Verify Connections

```bash
python final_sos_verification.py
```

Checks:
- ✅ Patient → SOS Request connection
- ✅ SOS Request → Donor Responses connection
- ✅ Donation Tracking works
- ✅ Privacy rules enforced
- ✅ All relationships valid

---

## Key Features Implemented

✅ **Bidirectional Connection**
- Patient creates request
- Donors get matched and respond
- Full two-way communication

✅ **Privacy-First**
- Contact hidden by default
- Requires explicit donor consent
- Patient confirms reveal request

✅ **Multi-Channel**
- Web UI responses
- SMS responses
- Email notifications

✅ **Real-Time Tracking**
- Donation status updates
- GPS location tracking
- Live notifications

✅ **Role-Based Access**
- Patients see own requests/responses
- Donors see responses they gave
- Admins see everything

✅ **Data Integrity**
- OneToOne relationships prevent duplicates
- Unique constraints on request-donor pairs
- Cascading deletes for cleanup

---

## Common Scenarios

### Scenario 1: Patient Creates Request & Gets Response

1. Patient creates SOS for O+ blood
2. System matches 5 compatible donors in Delhi
3. Each donor gets SMS alert
4. Donor 1 replies "YES SHARE" via SMS
5. SOSResponse created with consent=True
6. Patient sees donor in response list
7. Patient calls reveal_contact → gets phone
8. Patient contacts donor directly

### Scenario 2: Donor Tracks Donation

1. Donor agrees to donate (YES)
2. DonationTracker created (AGREED)
3. Donor updates: "I'm TRAVELING" (with GPS)
4. Patient notified of status
5. Donor updates: "ARRIVED" at location
6. Donor updates: "DONATING in progress"
7. Donor updates: "COMPLETED"
8. Patient sees completion and thanks donor

### Scenario 3: Donor Declines

1. Donor receives SMS alert
2. Donor replies "NO"
3. SOSResponse created with response=NO
4. No tracker created
5. Patient sees decline
6. System continues matching other donors

---

## Configuration

### Environment Variables

```
# SMS Configuration
SMS_PROVIDER=fast2sms  # or textlocal
SMS_API_KEY=your_api_key
SMS_SENDER=VEINLN

# City Matching
CITY_MATCH_STRICT=1  # 1=strict, 0=loose
```

### Database Indexes

Optimized indexes for common queries:

```python
# sos/models.py
class SOSRequest(models.Model):
    class Meta:
        indexes = [
            models.Index(fields=["status", "blood_group_needed", "city"]),
            models.Index(fields=["created_at"]),
            models.Index(fields=["priority", "status"]),
        ]

class SOSResponse(models.Model):
    class Meta:
        indexes = [
            models.Index(fields=["request", "response"]),
            models.Index(fields=["donor", "response"]),
        ]
```

---

## Status: ✅ COMPLETE

All connections between patient SOS requests and donor responses are fully implemented and tested.

- ✅ Models created and migrated
- ✅ API endpoints working
- ✅ Serializers complete with privacy rules
- ✅ Views connected and notifying
- ✅ SMS bidirectional flow implemented
- ✅ Donation tracking active
- ✅ Privacy enforced
- ✅ All tests passing
- ✅ Documentation complete

**The system is ready for production use!**
