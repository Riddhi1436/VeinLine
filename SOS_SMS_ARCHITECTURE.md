# 🔄 SOS SMS Flow - Complete Architecture

## System Overview

```
Patient Creates SOS
        ↓
   Form Submission
        ↓
   CreateSOSView.post()
        ↓
   SOSRequest created in DB
        ↓
   match_donors_for_request()
        ↓
   Filter by:
   - Compatible blood group
   - Same city (case-insensitive)
   - is_available = True
        ↓
   For each matched donor:
   ├─ Create SOSResponse (pending)
   ├─ Send SMS via Fast2SMS/Textlocal
   ├─ Send email (fallback)
   └─ Log result
        ↓
   Show success message to patient
        ↓
   Donor receives SMS & email
        ↓
   Donor replies (YES/NO)
        ↓
   Patient notified
```

## Detailed Components

### 1. **Form Submission**
**File:** [templates/create_sos.html](templates/create_sos.html)

```html
<form method="POST" action="/sos/create/">
    <input name="blood_group_needed" required>
    <input name="units_needed" type="number" min="1" max="10">
    <input name="city" required>
    <input name="area">
    <input name="hospital_name">
    <textarea name="message"></textarea>
    <button type="submit">Create SOS Request</button>
</form>
```

### 2. **View Processing**
**File:** [webui/views.py](webui/views.py) - `CreateSOSView` class

```python
class CreateSOSView(RoleRequiredMixin, TemplateView):
    def post(self, request):
        # 1. Parse form data
        blood_group = request.POST.get('blood_group_needed')
        units = int(request.POST.get('units_needed'))
        city = request.POST.get('city')
        
        # 2. Validate inputs
        if not blood_group or not city:
            return error_response
        
        # 3. Create SOSRequest
        sos_request = SOSRequest.objects.create(
            requester=request.user,
            blood_group_needed=blood_group,
            units_needed=units,
            city=city,
            status='open',
        )
        
        # 4. Find matching donors
        donors = match_donors_for_request(sos_request, limit=50)
        
        # 5. Notify each donor
        for donor in donors:
            # Create response record
            SOSResponse.objects.create(
                request=sos_request,
                donor=donor.user,
                response='pending',
                channel='sms'
            )
            
            # Send SMS
            phone = donor.user.profile.phone_e164
            message = f"VeinLine SOS: Need {blood_group}..."
            send_sms(phone, message)
            
            # Send email (fallback)
            send_fallback_email(donor.user.email, message)
        
        # 6. Redirect to dashboard
        return redirect('patient-dashboard')
```

### 3. **Donor Matching**
**File:** [sos/services.py](sos/services.py) - `match_donors_for_request()`

```python
def match_donors_for_request(sos_request, limit=50):
    # 1. Get compatible blood groups
    # O+ needs: O- or O+
    # AB+ needs: Anyone
    groups = compatible_donor_groups(sos_request.blood_group_needed)
    
    # 2. Filter by criteria
    donors = DonorDetails.objects.filter(
        blood_group__in=groups,              # Compatible blood group
        city__iexact=sos_request.city,       # Same city (case-insensitive)
        is_available=True                    # Must be available
    ).select_related('user').order_by('-updated_at')[:limit]
    
    return donors
```

**Blood Group Compatibility:**
```python
DEFAULT_COMPATIBILITY = {
    "O-": {"O-"},
    "O+": {"O-", "O+"},
    "A-": {"O-", "A-"},
    "A+": {"O-", "O+", "A-", "A+"},
    "B-": {"O-", "B-"},
    "B+": {"O-", "O+", "B-", "B+"},
    "AB-": {"O-", "A-", "B-", "AB-"},
    "AB+": {"O-", "O+", "A-", "A+", "B-", "B+", "AB-", "AB+"},
}
```

### 4. **SMS Sending**
**File:** [core/services/sms.py](core/services/sms.py) - `send_sms()`

```python
def send_sms(phone_e164: str, message: str) -> dict:
    # 1. Get configuration
    api_key = settings.VEINLINE_SMS_API_KEY  # Must be set!
    provider = settings.VEINLINE_SMS_PROVIDER  # 'fast2sms' or 'textlocal'
    
    # 2. Validate phone
    if not phone_e164 or not is_valid_e164(phone_e164):
        return {"ok": False, "reason": "invalid_phone"}
    
    # 3. Send via provider
    if provider == 'fast2sms':
        # Call Fast2SMS API
        response = requests.post(
            'https://www.fast2sms.com/dev/bulkV2',
            headers={'authorization': api_key},
            data={
                'route': 'v3',
                'numbers': phone_e164.lstrip('+'),
                'message': message,
            }
        )
    elif provider == 'textlocal':
        # Call Textlocal API
        response = requests.post(
            'https://api.textlocal.in/send/',
            data={
                'apikey': api_key,
                'numbers': phone_e164.lstrip('+'),
                'message': message,
            }
        )
    
    # 4. Return result
    if response.status_code == 200:
        return {"ok": True, "provider": provider}
    else:
        return {"ok": False, "reason": "provider_error"}
```

### 5. **Database Models**
**File:** [sos/models.py](sos/models.py)

```python
class SOSRequest(models.Model):
    id                  # Unique ID
    requester           # Patient who created it
    blood_group_needed  # O+, AB-, etc.
    units_needed        # 1-10
    city                # Mumbai, Delhi, etc.
    area                # Bandra, Bhayandar (optional)
    hospital_name       # Which hospital
    message             # Emergency details
    status              # OPEN, FULFILLED, CLOSED
    priority            # NORMAL, URGENT, CRITICAL
    created_at
    sms_reply_token     # For SMS reply parsing
    
class SOSResponse(models.Model):
    request             # FK to SOSRequest
    donor               # FK to User
    response            # pending, accepted, declined
    channel             # 'sms', 'email', 'app'
    created_at
    updated_at

class DonorDetails(models.Model):
    user                # FK to User
    blood_group         # O+, AB-, etc.
    city                # Mumbai, Delhi, etc.
    area                # Bandra, Bhayandar
    is_available        # True/False (donor marked available)
    medical_history     # String
```

## Logging Points

The system logs at key points to help debugging:

```
[SOS #123] Created by patient_name for O+ in Mumbai
[SOS #123] Starting donor matching for O+ in Mumbai
[SOS #123] Found 5 matching donors
[SOS #123] Sending SMS to donor1 (+919876543210)
[SOS #123] ✓ SMS sent to donor1
[SOS #123] Sending SMS to donor2 (+919876543211)
[SOS #123] ✗ SMS failed for donor2: invalid_phone
[SOS #123] Donor donor3 has no phone number
[SOS #123] Summary: Found 5 matching donors. Notifications sent to 3 (1 donors missing phone) (1 SMS failures)
```

## Configuration Required

**Environment Variables (.env):**
```env
# SMS Configuration
VEINLINE_SMS_API_KEY=your_fast2sms_api_key    # From Fast2SMS dashboard
VEINLINE_SMS_PROVIDER=fast2sms                 # 'fast2sms' or 'textlocal'
VEINLINE_SMS_SENDER=VEINLN                     # Sender name (11 chars max)

# City matching
VEINLINE_CITY_MATCH_STRICT=True                # Strict city matching
```

## Data Flow - Example

**Step 1: Patient Creates SOS**
```
POST /sos/create/
{
    "blood_group_needed": "O+",
    "units_needed": 2,
    "city": "Mumbai",
    "area": "Bandra",
    "hospital_name": "Lilavati",
    "message": "Emergency blood needed"
}
```

**Step 2: Database Insertion**
```
SOSRequest #123 created:
- requester: patient_john
- blood_group_needed: O+
- units_needed: 2
- city: Mumbai
- status: OPEN
```

**Step 3: Donor Matching Query**
```sql
SELECT * FROM donations_donordetails
WHERE blood_group IN ('O-', 'O+')
  AND LOWER(city) = 'mumbai'
  AND is_available = TRUE
LIMIT 50
```

**Result:**
```
- donor1 (O+, Mumbai, Bandra) - Has phone
- donor2 (O+, Mumbai, Andheri) - Has phone
- donor3 (O-, Mumbai, Fort) - No phone
```

**Step 4: Notifications Sent**
```
SOSResponse #1: donor1 → SMS sent ✓
SOSResponse #2: donor2 → SMS sent ✓
SOSResponse #3: donor3 → Email only (no phone)

SMS Message to donors:
"VeinLine SOS: Need O+ blood in Mumbai. 
 Reply: YES xyz123 or NO xyz123."
```

**Step 5: Response Tracking**
```
Donor1 replies: "YES xyz123"
Donor2 replies: "NO xyz123"
Donor3 ignores

SOSRequest status updates:
- SOSResponse #1: accepted
- SOSResponse #2: declined
- SOSResponse #3: no_response

Patient dashboard shows: 2 donors responded, 1 accepted, 1 declined
```

## Success Criteria

✅ SOS SMS is working when:

1. **Patient creates SOS** → No errors, shows success message
2. **Form shows donors found** → "Found X matching donors"
3. **Notifications sent** → "Notifications sent to Y donors"
4. **Donors have phone** → Profile shows phone_e164 field filled
5. **Donor receives SMS** → SMS arrives on phone (if real API key)
6. **Logs show details** → `[SOS #X]` lines visible in Django logs
7. **Database updated** → SOSResponse records created for each donor
8. **No errors** → CreateSOSView completes without exceptions

## Troubleshooting Checklist

| Check | Command | Expected |
|-------|---------|----------|
| SMS API Key Set | `echo $VEINLINE_SMS_API_KEY` | Shows key (or empty for dev) |
| Donors Exist | `python manage.py shell` → `DonorDetails.objects.count()` | > 0 |
| Donors Available | `DonorDetails.objects.filter(is_available=True).count()` | > 0 |
| Donors Have Phone | `DonorDetails.objects.exclude(user__profile__phone_e164='').count()` | > 0 |
| City Match | Compare `sos.city` with `donor.city` (case-insensitive) | Exact match |
| SMS Test | `send_sms('+919876543210', 'Test')` | Returns `{'ok': True}` |
| Form Accessible | Visit http://localhost:8000/sos/create/ | Form loads |
| Form Submits | Fill and submit form | Redirects to dashboard |
| SOS Created | Check database | SOSRequest record exists |
| Donors Matched | Check database | SOSResponse records created |

## API Endpoints

**Create SOS (Web Form):**
```
POST /sos/create/
Content-Type: application/x-www-form-urlencoded

blood_group_needed=O+
&units_needed=2
&city=Mumbai
&area=Bandra
&hospital_name=Lilavati
&message=Emergency
```

**Match Donors (API):**
```
POST /api/sos/match/
Content-Type: application/json

{
    "sos_request_id": 123
}
```

**List My SOS:**
```
GET /api/sos/my-requests/
```

## Related Files

```
webui/
  ├─ views.py          ← CreateSOSView
  └─ urls.py           ← /sos/create/ route

sos/
  ├─ models.py         ← SOSRequest, SOSResponse
  ├─ services.py       ← match_donors_for_request()
  ├─ views.py          ← API endpoints
  └─ urls.py

core/
  ├─ services/
  │  └─ sms.py         ← send_sms()
  └─ constants.py      ← BloodGroup compatibility

donations/
  └─ models.py         ← DonorDetails

templates/
  ├─ create_sos.html   ← SOS form
  ├─ base.html
  └─ dashboards/
     └─ patient.html   ← "Create SOS" button

accounts/
  └─ models.py         ← Profile with phone_e164

check_sms_debug.py     ← Diagnostic script
SMS_DEBUGGING_GUIDE.md ← Troubleshooting guide
```

---
**Last Updated:** 2024
**Version:** 1.0
