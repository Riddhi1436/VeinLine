# 🚨 Create SOS - Quick Start

## What's New? 
Patients can now create emergency blood requests directly from the web! No API needed.

## How to Access

### From Patient Dashboard:
1. **Login** with patient account
2. Click **Patient Dashboard** (from user menu)
3. Click the red **🚨 Create Emergency SOS** button OR
4. Click **Create now →** in the Quick Create card

### Direct Link:
```
/sos/create/
```

---

## 5-Minute Setup

### Step 1: Update Your Profile (One-time)
Go to Settings and add:
- ✅ Phone number (E.164 format: +919876543210)
- ✅ City name
- ✅ Area/Locality (optional)

### Step 2: Create SOS
1. Go to /sos/create/
2. Select blood group (O+, A-, etc.)
3. Enter units needed (1-10)
4. Choose priority level (Normal/Urgent/Critical)
5. Enter city
6. Click **Create**

### Step 3: Done!
System automatically:
- ✅ Creates SOS request
- ✅ Finds matching donors
- ✅ Sends SMS alerts
- ✅ Updates dashboard

---

## Form Fields

| Field | Example | Notes |
|-------|---------|-------|
| Blood Group | O+ | Required - 8 options |
| Units | 2 | 1-10 (each = 450ml) |
| Priority | URGENT | Normal/Urgent/Critical |
| City | Bangalore | Required - must match donors |
| Area | Indiranagar | Optional but helpful |
| Hospital | Apollo Hospital | Optional |
| Message | Surgery at 3PM | Optional - helps donors |

---

## What Happens?

```
You Create SOS
    ↓
Form Submitted
    ↓
SOS Created in Database (#123)
    ↓
System Finds Compatible Donors
    ↓
SMS Sent: "Need O+ blood in Bangalore. Reply YES or NO"
    ↓
Donors Respond
    ↓
You Get Notified
    ↓
Contact Responding Donors
    ↓
Blood Transfer Arranged ✅
```

---

## Response Times

| Priority | Typical Time |
|----------|------------|
| 🔴 Critical | 30 min - 2 hours |
| 🟠 Urgent | 2 - 12 hours |
| 🔵 Normal | 12 - 48 hours |

---

## FAQ

**Q: Do I need an API key?**
A: No! Everything works from the web interface now.

**Q: Can I create multiple SOS?**
A: Yes! Each SOS is independent.

**Q: Will my phone be shared?**
A: No. Only with donors who explicitly consent.

**Q: What if no donors found?**
A: Try again with Normal priority - it reaches more donors over time.

**Q: Can I edit after creating?**
A: Not yet - create a new one if needed.

---

## Direct Links

- **Create SOS**: `/sos/create/`
- **Patient Dashboard**: `/dashboard/patient/`
- **SOS Status**: Check dashboard for list

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Form won't submit | Fill all required fields |
| Not a patient | Create patient account first |
| No donor found | Wrong city/blood group/donors unavailable |
| SMS not sending | SMS service not configured (check with admin) |

---

## Blood Group Compatibility

Need O+? Can receive from: O-, O+
Need AB+? Can receive from: Anyone

See full chart in the form.

---

## 🎯 Best Practice

1. ✅ Specify city exactly
2. ✅ Be honest about priority
3. ✅ Add helpful details in message
4. ✅ Respond quickly to donors
5. ✅ Say thanks!

---

**Done!** You're ready to create an SOS. 

👉 [Create Emergency SOS Now](/sos/create/)
