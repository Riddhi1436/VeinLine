# 📱 Donor SOS Dashboard - How to Find & Respond to SOS Requests

## Overview

Donors now have a clear, easy-to-use interface to find SOS (emergency blood) requests from patients in their area.

## For Donors - How to Use

### Step 1: Login to Your Account
- Go to: http://localhost:8000
- Login with your donor credentials

### Step 2: Go to Donor Dashboard
- Click "Donor Dashboard" or go to: http://localhost:8000/donor-dashboard

### Step 3: View Available SOS Requests
You'll see:
- **🔴 Critical (Immediate)** - Highest priority, needs blood NOW
- **🟠 Urgent (24 hours)** - High priority, needed within 24 hours  
- **🔵 Normal** - Regular request

### Step 4: Find SOS Requests Near You
Dashboard shows SOS requests in your city with:
- **Blood Group Needed** - O+, A-, etc. (shown in red)
- **Units Needed** - How many units needed
- **Location** - City and area
- **Hospital** - Where to donate
- **Patient Message** - What patient wrote
- **Priority** - How urgent
- **Time** - When it was created

### Step 5: Respond to SOS
Click on any SOS request to:
1. **View Full Details**
   - Patient's blood group preference
   - Hospital details
   - Exact location
   - Special message

2. **See Other Donors' Responses**
   - How many accepted
   - How many declined
   - Overall status

3. **Respond: YES or NO**
   - **YES** = "I can donate"
   - **NO** = "I cannot donate"

### Step 6: Share Contact Information (Optional)
If you say YES:
- You'll be asked if patient can contact you
- You can share your phone number
- Or keep it private (patient can't call)

---

## Admin View - How to Manage SOS Requests

### Access Admin Dashboard
- Go to: http://localhost:8000/admin
- Login with admin credentials
- Click "Sos Requests" in sidebar

### What You'll See

#### List View
Shows all SOS requests with color-coded information:

| Column | Shows | What It Means |
|--------|-------|--------------|
| SOS ID | 🔷 SOS #123 | Unique request ID |
| Patient | john_doe | Who created the SOS |
| Blood | 🔴 O+ | Bright red box with blood type |
| Location | 📍 Mumbai, Bandra | City and area |
| Units | 2 units | How many units needed |
| Priority | 🔴 Critical | Urgency level |
| Status | 🟢 Open | Current state |
| Donors Notified | ✅ 5 responses | How many responded |
| Created | Feb 01, 14:30 | When it was created |

#### Color Coding

**Priority:**
- 🔴 **Critical** (Red) = Immediate, life-threatening
- 🟠 **Urgent** (Orange) = Within 24 hours
- 🔵 **Normal** (Blue) = Regular request

**Status:**
- 🟢 **Open** (Green) = Still accepting donations
- 🔵 **Fulfilled** (Blue) = Found enough donors
- 🔴 **Cancelled** (Red) = Request cancelled

**Blood Groups:**
- Coded by color for easy recognition
- Recipient blood type shown

**Donor Responses:**
- 🟢 0 = No responses yet
- 🟠 1-2 = Few responses
- 🟢 3+ = Multiple responses

---

## Filtering & Searching SOS Requests

### Filter By
- **Status:** Open / Fulfilled / Cancelled
- **Priority:** Normal / Urgent / Critical
- **Blood Group:** O+ / O- / A+ / A- / B+ / B- / AB+ / AB-
- **City:** Mumbai / Delhi / Bangalore / etc.
- **Date:** When it was created

### Search By
Type in search box to find:
- City name (e.g., "Mumbai")
- Area (e.g., "Bandra")
- Hospital name (e.g., "Lilavati")
- Patient message
- Patient username
- Patient email

---

## Viewing SOS Details

### Click on Any SOS to See:

#### 1. Emergency Details
- SOS ID
- Patient name & contact
- Blood group needed
- Units needed
- Priority level

#### 2. Location
- City
- Area
- Hospital name
- Address (if provided)

#### 3. Patient's Message
- What patient wrote
- Additional context
- Special instructions

#### 4. Status & Donor Responses
- Current status (Open/Fulfilled/Cancelled)
- How many donors responded
- Breakdown:
  - ⏳ Still thinking (Pending)
  - ✅ Will donate (Accepted)
  - ❌ Cannot donate (Declined)

#### 5. All Responses
Click link to see:
- Which donors responded
- Their response (Yes/No)
- Via which channel (Web/SMS)
- When they responded

---

## Responding to SOS - Step by Step

### If You Can Help

1. **Read the SOS Details**
   - Check blood group
   - Check location (can you reach hospital?)
   - Check urgency
   - Read patient's message

2. **Check Your Eligibility**
   - Are you currently available?
   - Is your blood group compatible?
   - Can you reach the hospital?
   - Medical conditions ok?

3. **Click "YES, I Can Help"**
   - System records your response
   - Hospital can see you're available
   - Patient notified

4. **Share Contact (Optional)**
   - Patient may need to call you
   - You choose if they can see your phone
   - Private or shared - your choice

5. **Go to Hospital**
   - Get the hospital address
   - Bring ID
   - Follow hospital procedure
   - Save lives! 🩸

### If You Can't Help

1. **Click "NO, I Cannot Help"**
   - System records your response
   - Helps patient find other donors
   - No pressure, no judgment

2. **Optional: Tell Why**
   - Medical condition
   - Not available today
   - Location too far
   - Personal reasons

---

## Admin: Managing Donors' Responses

### View All Responses
Click "Sos Responses" in admin to see:
- Which donor responded
- What they said (Yes/No/Pending)
- Via SMS or Web
- Contact shared or private
- Response time

### Response Tracking
- **⏳ Pending** = Donor hasn't responded yet
- **✅ Yes** = Donor accepted (name shown in green)
- **❌ No** = Donor declined (name shown in red)

### Contact Management
- **🟢 Shared** = Patient can see donor's phone
- **🔒 Private** = Patient cannot see contact

---

## SMS Notifications for Donors

When there's an SOS request, donors get SMS like:

```
VeinLine SOS: Need O+ blood in Mumbai.
Reply: YES <token> or NO <token>
```

Donors can reply:
- **SMS: "YES xyz123"** → I can donate
- **SMS: "NO xyz123"** → I cannot donate

This works even without internet!

---

## Admin Dashboard Statistics

On admin dashboard, you'll see:
- Total SOS requests
- By status (open, fulfilled, cancelled)
- By priority (critical, urgent, normal)
- Donor response rates
- Response channels (web, SMS)
- Blood bank inventory

---

## Troubleshooting

### "I'm not seeing any SOS requests"

**Check:**
1. Are you logged in as a donor?
2. Is your city set in profile?
3. Are there SOS requests in your city?
4. Check Admin → SOS Requests to see all

**Fix:**
- Update your profile with correct city
- Check if there are any open requests
- Contact admin if requests not showing

### "SOS not showing my response"

**Check:**
1. Did you actually click YES/NO?
2. Internet connection ok?
3. Try refreshing page

**Fix:**
- Refresh page (F5)
- Click response again
- Check if it shows in admin

### "Can't see patient's contact"

**Expected:**
- Patient contact is only shown if donor shares consent
- This is for privacy protection

**To share:**
1. Respond YES to SOS
2. Check "Share my contact"
3. Patient can now see your phone

---

## For Admins: Troubleshooting

### "AttributeError on admin page" ❌
**Fixed!** The admin interface has been completely rebuilt with proper fields and readonly attributes.

### "Can't see all SOS requests" 
**Try:**
1. Use filters (Status, Priority, City, Date)
2. Use search (Hospital, City, Patient name)
3. Check pagination

### "Response count wrong"
**Check:**
1. Go to "SOS Responses" to see all
2. Filter by specific request
3. Manual count should match

### "Want to create SOS in admin"
**You can:**
1. Go to "SOS Requests"
2. Click "Add SOS Request"
3. Fill in details
4. Save
(But usually patients create via form)

---

## Features by Role

### Donors Can:
- ✅ View SOS requests in their city
- ✅ Filter by blood group, priority, status
- ✅ Respond YES or NO
- ✅ Share contact info (optional)
- ✅ See donor response status
- ✅ Receive SMS notifications

### Patients Can:
- ✅ Create SOS requests
- ✅ See which donors responded
- ✅ See donor contact (if they shared)
- ✅ Track SOS status
- ✅ Update SOS details

### Admins Can:
- ✅ View all SOS requests
- ✅ See all donor responses
- ✅ Filter and search
- ✅ Create SOS (if needed)
- ✅ Delete SOS (if needed)
- ✅ Monitor system health
- ✅ See statistics

---

## Quick Reference

### URLs
| Page | URL |
|------|-----|
| Donor Dashboard | /donor-dashboard |
| Admin SOS List | /admin/sos/sosrequest/ |
| Admin SOS Responses | /admin/sos/sosresponse/ |
| Create SOS (Patient) | /sos/create/ |

### Color Codes
| Color | Meaning |
|-------|---------|
| 🔴 Red | Critical / High Priority / Blood Color |
| 🟠 Orange | Urgent |
| 🔵 Blue | Normal / Info |
| 🟢 Green | Open / Available / Accepted |
| ⚪ Gray | Cancelled / Offline |

### Emojis
| Emoji | Means |
|-------|-------|
| 📍 | Location |
| 🩸 | Blood |
| ✅ | Yes / Accepted |
| ❌ | No / Declined |
| ⏳ | Pending |
| 📱 | SMS |
| 🌐 | Web |
| 🔒 | Private |

---

## Privacy & Security

### Patient Privacy
- Phone number hidden until donor shares consent
- Email visible only to donors
- Message only visible to matched donors
- SMS reply token protects against abuse

### Donor Privacy  
- Can choose to share or hide contact
- Response private until they share
- SMS allows anonymous response
- Medical info not shared

---

## Performance Tips

### For Admins
- Use filters to narrow down
- Search by specific city/hospital
- Sort by date to find recent
- Use "Display X items" to control list size

### For Donors
- Check notifications daily
- Update your city in profile
- Mark as available if you can donate
- Respond quickly to help patients

---

## Next Features (Future)

Planned improvements:
- Real-time notifications
- Chat between donor/patient
- Donor calling patient
- Automatic donation scheduling
- Blood bank integration
- Rating system

---

**Last Updated:** 2024
**Version:** 1.0
**Status:** Production Ready

For technical issues, contact admin or check logs.
