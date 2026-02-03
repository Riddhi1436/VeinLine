# VeinLine - New Features Quick Setup & Testing Guide

## 🚀 Quick Setup

### 1. Apply Migrations

```powershell
python manage.py migrate
```

This will create all the tables for:
- DonorStatistics (badges & leaderboard)
- Appointments & HealthQuestionnaire
- Notifications & NotificationPreference
- BloodBank locations
- DonorFeedback
- SOS priority levels

### 2. Create Test Data (Optional)

```powershell
# Create some sample blood banks
python manage.py shell
```

```python
from core.models import BloodBank

banks = [
    BloodBank(
        name="Red Crescent Blood Bank",
        city="Mumbai",
        address="123 Medical Lane, Mumbai",
        latitude=19.0760,
        longitude=72.8777,
        phone="+91-22-1234-5678",
        email="mumbai@redcrescent.org",
        opening_time="08:00",
        closing_time="18:00",
        accepts_walk_in=True,
        has_emergency_service=False
    ),
    BloodBank(
        name="City Hospital Blood Bank",
        city="Delhi",
        address="456 Hospital St, Delhi",
        latitude=28.6139,
        longitude=77.2090,
        phone="+91-11-9876-5432",
        email="delhi@cityhospital.org",
        opening_time="07:00",
        closing_time="20:00",
        accepts_walk_in=True,
        has_emergency_service=True
    ),
]

for bank in banks:
    bank.save()

exit()
```

### 3. Start the Server

```powershell
python manage.py runserver
```

---

## 📋 Feature Testing Checklist

### ✅ Feature 1: Donor Leaderboard & Badges
- [ ] Navigate to `/leaderboard/` - See top donors
- [ ] Search by city: `/leaderboard/` → "By City" button
- [ ] Search by blood group: `/leaderboard/` → "By Blood Group" button
- [ ] View available badges section at bottom
- [ ] Check API: `GET /api/donations/leaderboard/top_donors/`
- [ ] Check your stats: `GET /api/donor/stats/` (authenticated)

**Test Data**: Create 5-10 donors with different donation counts to see badges awarded

### ✅ Feature 2: Appointment Scheduling
- [ ] Navigate to `/appointments/`
- [ ] Search for slots by city
- [ ] Click "Book Now" on a slot
- [ ] Fill out health questionnaire
- [ ] Confirm appointment
- [ ] View "My Appointments" section
- [ ] Test cancel/confirm actions
- [ ] Check eligibility logic (answer "Yes" to disqualifying conditions)

**Test Data Needed**: Create AppointmentSlot records in Django admin

```sql
-- Or via Django shell:
from appointments.models import AppointmentSlot
from datetime import datetime, timedelta

slot = AppointmentSlot(
    blood_bank='red_crescent',
    city='Mumbai',
    address='123 Medical Lane',
    date=datetime.now().date() + timedelta(days=7),
    start_time='09:00',
    end_time='12:00',
    max_donors=20,
    status='available'
)
slot.save()
```

### ✅ Feature 3: Notification System
- [ ] Navigate to `/api/notifications/` (authenticated)
- [ ] Check unread count: `GET /api/notifications/unread_count/`
- [ ] Get preferences: `GET /api/notifications/preferences/`
- [ ] Update preferences: `PATCH /api/notifications/preferences/`
- [ ] Trigger notifications through other features:
  - [ ] Create appointment (appointment reminder)
  - [ ] Earn badge (achievement notification)
  - [ ] Receive feedback (thank you notification)

**API Testing**:
```bash
# Get all notifications
curl -H "Authorization: Bearer YOUR_TOKEN" http://localhost:8000/api/notifications/

# Mark as read
curl -X POST -H "Authorization: Bearer YOUR_TOKEN" \
  http://localhost:8000/api/notifications/1/mark_as_read/

# Get preferences
curl -H "Authorization: Bearer YOUR_TOKEN" \
  http://localhost:8000/api/notifications/preferences/
```

### ✅ Feature 4: Blood Bank Finder Map
- [ ] Navigate to `/blood-banks/`
- [ ] Should see interactive map with all banks
- [ ] Search by city: Enter city name, click "Search by City"
- [ ] Search nearby: Click "Search Nearby" (uses geolocation)
- [ ] View open now: Click "Open Now" button
- [ ] Click on bank to see details
- [ ] Check API endpoints:
  - [ ] `GET /api/blood-banks/` - All banks
  - [ ] `GET /api/blood-banks/by_city/?city=Mumbai`
  - [ ] `GET /api/blood-banks/open_now/`
  - [ ] `GET /api/blood-banks/nearby/?lat=19.07&lon=72.87&radius=50`

### ✅ Feature 5: Medical Eligibility Checker
- [ ] Navigate to `/eligibility/`
- [ ] Answer "No" to all questions → Should see "Eligible" result
- [ ] Answer "Yes" to "Do you have fever?" → Should see "Not Eligible"
- [ ] Answer "Yes" to "Have you had tattoo in 3 months?" → Should see temporary condition
- [ ] Click "Check Again" to restart
- [ ] Click "Book Appointment" → Should redirect to `/appointments/`

### ✅ Feature 6: Activity Timeline
- [ ] Authenticate and navigate to `/timeline/`
- [ ] Should see stats cards:
  - [ ] Total Donations (from appointments)
  - [ ] Lives Saved (from stats)
  - [ ] Badges Earned (from stats)
  - [ ] Average Rating (from feedback)
- [ ] Should see timeline events (if any)
- [ ] Complete an appointment as "completed" to see timeline update

### ✅ Feature 7: Emergency Mode SOS
- [ ] Create an SOS request with `priority="critical"`
- [ ] Check in admin: See colored indicators (🔴 Critical)
- [ ] Create an SOS request with `priority="urgent"`
- [ ] Create an SOS request with `priority="normal"`
- [ ] Query API with priority filter
- [ ] Verify critical requests are sorted first

**Via Django Shell**:
```python
from sos.models import SOSRequest
from django.contrib.auth.models import User

user = User.objects.first()
sos = SOSRequest(
    requester=user,
    blood_group_needed='O+',
    units_needed=1,
    city='Mumbai',
    hospital_name='City Hospital',
    priority='critical'  # Test this
)
sos.save()
```

### ✅ Feature 8: Donor Feedback/Testimonials
- [ ] Authenticate as a patient
- [ ] Navigate to `/api/feedback/` (POST method)
- [ ] Leave feedback on a donor:

```json
{
  "donor": 2,
  "rating": 5,
  "message": "Great donor! Very professional service.",
  "is_public": true
}
```

- [ ] Check feedback stats: `GET /api/feedback/stats/?donor_id=2`
- [ ] View all feedback for donor: `GET /api/feedback/?donor_id=2`
- [ ] Donor sees their feedback: `GET /api/feedback/my_feedback/` (authenticated)
- [ ] Check notification sent to donor

---

## 🔧 API Testing with cURL

### Get JWT Token
```bash
curl -X POST http://localhost:8000/api/auth/token/ \
  -H "Content-Type: application/json" \
  -d '{"username":"testuser","password":"testpass"}'
```

### Test Leaderboard
```bash
# Top donors
curl http://localhost:8000/api/donations/leaderboard/top_donors/

# By city
curl "http://localhost:8000/api/donations/leaderboard/by_city/?city=Mumbai"

# By blood group
curl "http://localhost:8000/api/donations/leaderboard/by_blood_group/?blood_group=O%2B"
```

### Test Appointments
```bash
# List available slots
curl http://localhost:8000/api/slots/

# Upcoming slots
curl http://localhost:8000/api/slots/upcoming/

# Book appointment (requires auth)
curl -X POST http://localhost:8000/api/my-appointments/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"slot_id": 1}'
```

### Test Notifications
```bash
# Get unread count
curl -H "Authorization: Bearer YOUR_TOKEN" \
  http://localhost:8000/api/notifications/unread_count/

# Get all notifications
curl -H "Authorization: Bearer YOUR_TOKEN" \
  http://localhost:8000/api/notifications/

# Mark as read
curl -X POST -H "Authorization: Bearer YOUR_TOKEN" \
  http://localhost:8000/api/notifications/1/mark_as_read/
```

### Test Blood Banks
```bash
# All banks
curl http://localhost:8000/api/blood-banks/

# By city
curl "http://localhost:8000/api/blood-banks/by_city/?city=Mumbai"

# Open now
curl http://localhost:8000/api/blood-banks/open_now/

# Nearby (requires location)
curl "http://localhost:8000/api/blood-banks/nearby/?lat=19.07&lon=72.87&radius=50"
```

---

## 📊 Testing Scenarios

### Scenario 1: Complete Donation Journey
1. Check eligibility: `/eligibility/`
2. Find nearby bank: `/blood-banks/` → Search Nearby
3. Check open hours: View bank details
4. Book appointment: `/appointments/` → Select slot → Fill health form
5. View appointment: `/timeline/` → See scheduled appointment
6. Mark complete (admin): Django admin → Appointments → Mark as completed
7. Check activity updated: `/timeline/` → See donation in timeline

### Scenario 2: Donor Recognition
1. Make multiple donations: Complete 5+ appointments
2. Check leaderboard: `/leaderboard/`
3. Should see badges earned:
   - ✅ First Donation
   - ✅ 5 Donations
   - 🦸 Blood Hero (if 20+)
4. Patient leaves feedback: `/api/feedback/` (POST)
5. Check donor stats: `/api/donor/stats/` → See rating
6. Donor sees feedback: `/api/feedback/my_feedback/`

### Scenario 3: Emergency SOS
1. Create critical SOS: `priority="critical"`
2. System should prioritize:
   - Send urgent notifications
   - Show at top in queries
   - Trigger SMS alerts (if configured)
3. Donor responds to critical request
4. Earn "Emergency Responder" badge
5. Appear in top of leaderboard

---

## 🐛 Debugging Tips

### Check Migrations Applied
```bash
python manage.py showmigrations
```

### View All Notifications (as admin)
```
Django Admin → Notifications → Notification
```

### Create Test Donor Stats
```python
from donations.models import DonorStatistics
from django.contrib.auth.models import User

user = User.objects.get(username='testuser')
stats, created = DonorStatistics.objects.get_or_create(donor=user)
stats.total_donations = 5
stats.total_lives_saved = 15
stats.sos_responses = 3
stats.points = 250
stats.save()

# Check badges
new_badges = stats.check_badges()
print(new_badges)
```

### Send Test Notification
```python
from notifications.services import NotificationService
from notifications.models import NotificationType

NotificationService.create_notification(
    recipient=user,
    notification_type=NotificationType.SYSTEM,
    title="Test Notification",
    message="This is a test notification",
    icon="📧"
)
```

---

## 📱 Browser Console Testing

Open browser console (F12) and test APIs:

```javascript
// Get leaderboard
fetch('/api/donations/leaderboard/top_donors/')
  .then(r => r.json())
  .then(data => console.log(data))

// Get notifications (with auth)
fetch('/api/notifications/', {
  headers: {
    'Authorization': `Bearer ${localStorage.getItem('access_token')}`
  }
})
  .then(r => r.json())
  .then(data => console.log(data))

// Get blood banks
fetch('/api/blood-banks/')
  .then(r => r.json())
  .then(data => console.log(data))
```

---

## ✨ Success Indicators

✅ All features working when:
- [ ] Can view donor leaderboard with badges
- [ ] Can book and manage appointments
- [ ] Receive notifications for actions
- [ ] Can locate blood banks on map
- [ ] Eligibility checker works correctly
- [ ] Activity timeline shows donations
- [ ] SOS requests show priority levels
- [ ] Can leave and view feedback

---

**Last Updated**: January 30, 2026
**Status**: Ready for Testing ✅
