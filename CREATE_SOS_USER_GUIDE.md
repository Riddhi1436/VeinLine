# 🚨 Create SOS Feature - User Guide

## ✨ What's New?

Patients can now create emergency SOS requests directly from the web interface! No API calls needed.

## 🎯 How to Create an SOS

### Step 1: Log In
- Go to https://yourapp.com/login
- Login with your patient account

### Step 2: Go to Patient Dashboard
- Click on your username in the top right
- Select "🏥 Patient Dashboard"

### Step 3: Create Emergency SOS
- Click the red **🚨 Create Emergency SOS** button
- OR click **Create now →** in the Quick Create card

### Step 4: Fill Out the Form

#### Required Fields:

**🩸 Blood Group Needed**
- Select the blood group from dropdown
- Options: O+, O-, A+, A-, B+, B-, AB+, AB-

**📦 Units Needed**
- Enter number of units (1-10)
- 1 unit ≈ 450ml of blood

**⚡ Priority Level**
- 🔵 Normal - Can wait a few hours
- 🟠 Urgent - Needed within 24 hours  
- 🔴 Critical - Immediate (life-threatening)

**🏙️ City**
- Enter city where blood is needed
- Pre-filled with your city if available

#### Optional Fields:

**Area/Locality**
- Specific area in the city
- Helps donors locate you

**🏥 Hospital Name**
- Hospital where blood is needed
- Helps donors plan their visit

**💬 Additional Message**
- Any extra details for donors
- E.g., patient age, type of operation

### Step 5: Create SOS

Click **🚨 Create Emergency SOS** button

## ✅ What Happens Next?

```
1. System creates your SOS request
   ↓
2. Automatically finds compatible donors in your city
   ↓
3. Sends SMS alerts to matching donors
   ↓
4. Donors respond YES/NO via SMS or app
   ↓
5. You get notified of willing donors
   ↓
6. Contact donors to arrange blood transfer
```

## 📊 Track Your SOS

Your SOS requests appear in:
- **Patient Dashboard** - See all your SOS requests
- **Status Column** - Shows: OPEN, MATCHED, CANCELLED
- **Quick Stats** - "My Open SOS" card shows active requests

## 🚀 Features

### Automatic Donor Matching
✅ Finds donors with compatible blood group
✅ In same city (exact match)
✅ With available status = True
✅ Sends SMS immediately

### Smart Notifications
✅ SMS to all matching donors
✅ Email fallback if SMS fails
✅ Token-based reply system
✅ No passwords sent over SMS

### Privacy Controls
✅ Your phone is never shared without consent
✅ Only you and willing donors can contact each other
✅ Two-way consent required
✅ Secure communication

### Emergency Priority
✅ Critical priority: Donors notified ASAP
✅ Urgent priority: High visibility
✅ Normal priority: Regular queue

## 📱 Example SOS Creation

```
Blood Group: O+ (can donate to O+, A+, B+, AB+)
Units: 2 (900ml total)
Priority: URGENT (within 24 hours)
City: Bangalore
Area: Indiranagar
Hospital: Apollo Hospital
Message: Surgery scheduled at 3 PM, need urgent help

Result: System finds ~10 O+ donors in Bangalore
        Sends SMS to each: "Need O+ blood in Bangalore, reply YES or NO"
        2-3 donors typically respond within 1-2 hours
```

## ⏱️ Response Times

| Priority | Typical Response Time |
|----------|----------------------|
| 🔴 Critical | 30 minutes - 2 hours |
| 🟠 Urgent | 2 - 12 hours |
| 🔵 Normal | 12 - 48 hours |

*Actual response time depends on available donors in your city*

## 🆘 What If No Donors Found?

✅ You'll see a message: "No matching donors found"
✅ This doesn't mean donors don't exist - they might:
- Not be available right now
- Be outside your city
- Have incompatible blood group
- Not have phone numbers registered

**What to do:**
- Try creating a Normal priority SOS to reach more donors over time
- Update your city in profile settings
- Contact local blood banks directly
- Call emergency services if critical

## 🔄 Can I Create Multiple SOS?

Yes! You can create multiple SOS requests:
- For different blood groups
- For different locations
- At different times
- Each is independent

## ❌ Cancelling SOS

Coming soon: Cancel button to stop notifications and mark as cancelled.

For now, use the API or contact admin.

## 🔐 Security & Privacy

**Your Information:**
- Phone number: Only shared with explicit consent
- Email: Used for notifications only
- Profile: Visible only to system admins
- SOS Details: Only shared with matched donors

**Donor Information:**
- Protected until they consent
- Can control sharing with each donor request
- Two-way consent required to contact

**SMS:**
- Replies use token-based system (no passwords)
- Tokens rotate if abused
- Messages are not stored permanently

## 📖 FAQ

**Q: How many donors will be notified?**
A: Depends on compatible donors available in your city. Usually 5-50 donors.

**Q: Can I edit my SOS after creating?**
A: Not yet. You'll need to create a new one with updated info.

**Q: Is there a cost?**
A: No! SOS requests are completely free.

**Q: What if I get donors but don't need blood anymore?**
A: Cancel the SOS to stop further notifications.

**Q: Can family members create SOS for me?**
A: Not yet. Each person needs their own account.

**Q: What blood groups can I receive?**
A: Depends on your blood type. See chart in the form.

## 📞 Need Help?

- Check Hospital/Blood Bank directly
- Call Emergency Services (911/999)
- Contact VeinLine Support
- Use API if more options needed

## 🎯 Best Practices

**DO:**
✅ Be specific about location
✅ Mention priority accurately
✅ Add helpful details in message
✅ Respond quickly to donors
✅ Thank donors for helping

**DON'T:**
❌ Create fake/test SOS
❌ Misrepresent priority
❌ Ignore donor responses
❌ Share contact without consent
❌ Create multiple identical SOS

## 🚀 Quick Start

1. **Login** → Patient Account
2. **Dashboard** → Click 🚨 button
3. **Fill Form** → Blood group, city, priority
4. **Create** → SOS submitted
5. **Wait** → Donors notified automatically

Done! Donors will respond shortly.

---

**Status**: ✅ Live and Ready to Use
**Last Updated**: 2024-01-31
