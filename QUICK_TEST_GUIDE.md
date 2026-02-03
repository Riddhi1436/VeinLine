# Quick Testing Guide - VeinLine Appointment System

## 5-Minute Quick Start

### Step 1: Start the Server
```powershell
cd c:\Users\HP\Desktop\VeinLine
python manage.py runserver
```
Server starts at: http://localhost:8000/

### Step 2: Test Available Slots (No Login Required)
```bash
# In another terminal
curl http://localhost:8000/api/slots/upcoming/ | head -50
```
Expected: JSON array with ~1040 appointment slots

### Step 3: Create Test User & Get Token
```bash
# Get JWT token
curl -X POST http://localhost:8000/api/auth/token/ \
  -H "Content-Type: application/json" \
  -d '{"username":"apitestuser","password":"testpass123"}'
```
Expected: Returns `{"access": "eyJ...", "refresh": "..."}`

### Step 4: Book an Appointment
```bash
# Book appointment (replace TOKEN and SLOT_ID)
curl -X POST http://localhost:8000/api/my-appointments/ \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"slot_id": 1016}'
```
Expected: Returns appointment with ID and status "scheduled"

### Step 5: Submit Health Questionnaire
```bash
# Submit health form (replace TOKEN and APT_ID)
curl -X POST http://localhost:8000/api/appointments/1/health-questionnaire/ \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "has_fever": false,
    "has_cold_or_cough": false,
    "has_high_blood_pressure": false,
    "has_diabetes": false,
    "has_heart_condition": false,
    "has_cancer": false,
    "has_hiv_or_aids": false,
    "has_hepatitis": false,
    "has_bleeding_disorder": false,
    "is_pregnant": false,
    "is_breastfeeding": false,
    "recent_tattoo_or_piercing": false,
    "recent_surgery": false,
    "recent_blood_transfusion": false,
    "recent_vaccination": false,
    "takes_blood_thinners": false,
    "takes_antibiotics": false,
    "weight_kg": 70,
    "hemoglobin_level": 14.5,
    "additional_notes": "Test"
  }'
```
Expected: Returns questionnaire with `"is_eligible": true`

---

## Frontend Testing (Browser)

### Test 1: Browse Appointments
1. Open http://localhost:8000/appointments/
2. ✅ Should see "Book a Donation Appointment" heading
3. ✅ Should see search filters (City, Date)
4. ✅ Should see available slots loading (cards with blood bank info)
5. ✅ Should show ~1040 slots

### Test 2: Search Slots
1. Enter City: "Delhi"
2. Select Date: Any future date
3. Click "Search Slots"
4. ✅ Should show filtered results for Delhi

### Test 3: Register New User
1. Navigate to http://localhost:8000/register/
2. Fill form:
   - Username: testuser123
   - Email: test@example.com
   - Password: TestPass123
   - Role: Donor
3. Click Register
4. ✅ Should auto-login and redirect to home
5. ✅ Profile should be created

### Test 4: Book Appointment
1. Navigate to http://localhost:8000/appointments/
2. Click "Book Now" on any available slot
3. Modal should appear showing:
   - Blood bank name
   - Date
   - Time
4. Click "Confirm Booking"
5. ✅ Appointment should be created
6. ✅ Health questionnaire form should appear

### Test 5: Submit Health Questionnaire
1. Fill form:
   - Check some boxes (fever, pregnancy, etc.) set to unchecked
   - Leave some unchecked
   - Enter weight: 70 kg
   - Enter hemoglobin: 14.5
   - Add notes: "Test submission"
2. Click "Submit Health Questionnaire"
3. ✅ Form should be accepted
4. ✅ Success message should appear
5. ✅ Appointment should appear in "My Appointments" section

### Test 6: View My Appointments
1. Scroll down to "My Appointments" section
2. ✅ Should see your booked appointment
3. ✅ Should show:
   - Blood bank name
   - Date and time
   - Status badge (green "scheduled")
4. ✅ Should be able to see appointment details

---

## Using the Test Script

### Run Full API Test
```powershell
cd c:\Users\HP\Desktop\VeinLine
python test_api_endpoints.py
```

Expected output:
```
======================================================================
TESTING APPOINTMENT API ENDPOINTS
======================================================================

1. Testing GET /api/slots/upcoming/ (no auth)...
   Status: 200
   ✓ Got 1040 slots
   ...

3. Testing authentication...
   ✓ Got JWT access token

4. Testing POST /api/my-appointments/ (booking)...
   Status: 201
   ✓ Appointment created: ID X
   ...

5. Testing POST /api/appointments/X/health-questionnaire/...
   Status: 201
   ✓ Health questionnaire submitted
   ✓ Is eligible: True

6. Testing GET /api/my-appointments/...
   Status: 200
   ✓ Retrieved 1 appointment(s)
   ...

======================================================================
API TEST COMPLETE
======================================================================
```

---

## Browser Console Testing

### Check Console Logs
1. Open browser DevTools (F12)
2. Go to Console tab
3. Perform actions (load slots, book appointment, etc.)
4. ✅ Should see logs like:
   - "Loaded slots: 1040"
   - "Appointment created: {...}"
   - "Health Form Data: {...}"
   - NO red error messages

### Check Network Tab
1. Open DevTools → Network tab
2. Perform booking flow
3. ✅ Should see requests:
   - GET /api/slots/upcoming/ → 200
   - POST /api/my-appointments/ → 201
   - POST /api/appointments/*/health-questionnaire/ → 201
   - GET /api/my-appointments/ → 200

---

## Database Testing

### Check Appointment Creation
```bash
python -c "
import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'veinline_backend.settings')
django.setup()
from appointments.models import Appointment
for apt in Appointment.objects.all()[:5]:
    print(f'ID: {apt.id}, User: {apt.donor.username}, Slot: {apt.slot.blood_bank}, Status: {apt.status}')
"
```

### Check Health Questionnaires
```bash
python -c "
import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'veinline_backend.settings')
django.setup()
from appointments.models import HealthQuestionnaire
print(f'Total questionnaires: {HealthQuestionnaire.objects.count()}')
for q in HealthQuestionnaire.objects.all()[:3]:
    print(f'  - ID: {q.id}, Weight: {q.weight_kg}, Eligible: {q.is_eligible}')
"
```

---

## Troubleshooting

### Issue: "No available slots found"
**Solution**: Run `python create_sample_slots.py` to create sample data

### Issue: "401 Unauthorized" when booking
**Solution**: Make sure you're logged in and have valid JWT token

### Issue: "CSRF token missing" error
**Solution**: Token is automatically included in template, clear browser cache and reload

### Issue: Health form not accepting submission
**Solution**: Check browser console for validation errors, ensure all required fields are filled

### Issue: Appointment not appearing in "My Appointments"
**Solution**: 
- Check browser console for errors
- Verify user is logged in correctly
- Try refreshing the page

### Issue: "Slot not found" error
**Solution**: Use valid slot ID from the API response, slot must have status='available'

---

## Performance Testing

### Load 1040 Slots
```bash
time curl http://localhost:8000/api/slots/upcoming/ > /dev/null
```
Expected: < 200ms

### Search Filtering
```bash
time curl "http://localhost:8000/api/slots/by_city/?city=Delhi" > /dev/null
```
Expected: < 100ms

### Booking Request
```bash
curl -X POST http://localhost:8000/api/my-appointments/ \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"slot_id": 1016}' \
  --time-format '  Time: %{time_total}s'
```
Expected: < 0.2s

---

## Success Criteria

### ✅ All Tests Pass When:
1. Slots load without errors (1040 available)
2. Can register new user
3. Can login with JWT token
4. Can book appointment successfully
5. Health questionnaire form accepts data
6. Appointment appears in "My Appointments"
7. Browser console has no errors
8. Network requests return correct status codes
9. Database contains appointment and health data
10. Response times are under 200ms

---

## Quick Reference - API Endpoints

```bash
# Get slots (no auth)
GET http://localhost:8000/api/slots/upcoming/

# Get token
POST http://localhost:8000/api/auth/token/
Body: {"username": "...", "password": "..."}

# Book appointment (with token)
POST http://localhost:8000/api/my-appointments/
Auth: Bearer TOKEN
Body: {"slot_id": 1016}

# Submit health check (with token)
POST http://localhost:8000/api/appointments/{id}/health-questionnaire/
Auth: Bearer TOKEN
Body: {health data...}

# Get my appointments (with token)
GET http://localhost:8000/api/my-appointments/
Auth: Bearer TOKEN
```

---

## Support

If you encounter issues:
1. Check the browser console for error messages
2. Check the server logs (terminal where runserver is running)
3. Verify database has slots: `python create_sample_slots.py`
4. Check JWT token is valid (should not be expired)
5. Verify CSRF token is included (should be automatic)
6. Clear browser cache: Ctrl+Shift+Delete

**All tests completed successfully = System is working properly!**
