# SOS SMS Troubleshooting Flowchart

## 🔍 Is SMS Being Sent?

```
START: Run test_sos_sms_workflow.py
│
├─ Do you see "✓ SMS sent successfully"?
│  │
│  ├─ YES → ✅ SMS is working! Skip to "SMS Delivery Issues"
│  │
│  └─ NO → Did test script run at all?
│     │
│     ├─ NO (Python error) → See "Script Errors"
│     │
│     └─ YES (ran but SMS failed) → Continue below...
│
└─ Check: Is SMS_API_KEY set?
   │
   ├─ Not sure? → Run: echo $SMS_API_KEY
   │
   ├─ Empty? → ❌ Set SMS_API_KEY in .env and restart
   │           export SMS_API_KEY=your_key
   │           python test_sos_sms_workflow.py
   │
   └─ Set? → Check SMS_PROVIDER
      │
      ├─ Is SMS_PROVIDER set to fast2sms or textlocal?
      │  │
      │  ├─ NO → ❌ Set SMS_PROVIDER=fast2sms in .env
      │  │
      │  └─ YES → Check if API key is VALID
      │     │
      │     ├─ Unsure? → Visit provider dashboard (Fast2SMS/Textlocal)
      │     │            Log in and verify key works
      │     │
      │     ├─ Key invalid → ❌ Update SMS_API_KEY
      │     │
      │     └─ Key valid → Continue below...
      │
      └─ Check if donors have phone numbers
         │
         ├─ Run in Django shell:
         │  from accounts.models import Profile
         │  Profile.objects.filter(role='donor').exclude(phone_e164='').count()
         │
         ├─ Result is 0? → ❌ Create donors with phone numbers
         │               See "Creating Test Data"
         │
         └─ Result > 0? → Check phone number format
            │
            └─ Must be E.164: +<country><number>
               Examples: +919876543210, +14155552671
               │
               ├─ Format wrong? → ❌ Update to E.164 format
               │
               └─ Format correct? → Check if city matches
                  │
                  ├─ SOS city = "Bangalore"
                  │  Donor city = "bangalore" → ❌ MISMATCH (case-sensitive)
                  │               Fix: Use exact same case
                  │
                  └─ Cities match? → Check donor is_available
                     │
                     ├─ is_available = False → ❌ Set to True
                     │
                     └─ is_available = True → Check blood group
                        │
                        ├─ Incompatible groups? → ❌ Update to compatible group
                        │  (O- can donate to anyone, O+ to O+/A+/B+/AB+)
                        │
                        └─ All checks pass? → Check logs for API errors
                           │
                           ├─ Enable debug logging:
                           │  - Add print(result) after send_sms()
                           │  - Check what error API returned
                           │
                           ├─ Error: "invalid_api_key"? → ❌ API key wrong
                           │
                           ├─ Error: "timeout"? → Network issue
                           │                     Try again or check internet
                           │
                           ├─ Error: "invalid_phone"? → Phone format wrong
                           │
                           ├─ Error: "provider_error"? → SMS service down
                           │                             Contact provider
                           │
                           └─ Still stuck? → Email support with:
                              - Output of test script
                              - .env SMS settings (no key)
                              - Database user count
```

## 🚫 No Matching Donors Found?

```
START: test_sos_sms_workflow.py shows "Found 0 matching donors"
│
├─ Reason 1: No donors created yet
│  └─ Run: python manage.py shell
│     Then copy-paste code from "Creating Test Data" section
│
├─ Reason 2: Donors in different city
│  │
│  └─ Check city match:
│     In test script, donors use city='Bangalore'
│     SOS uses city='Bangalore'
│     │
│     ├─ Same? → Continue below
│     └─ Different? → ❌ Change one to match other
│
├─ Reason 3: Donors not available
│  │
│  └─ Check: is_available=True for all donors
│     Run: from donations.models import DonorDetails
│          DonorDetails.objects.filter(is_available=False)
│     │
│     ├─ Results show donors? → ❌ Set is_available=True
│     └─ No results? → Continue below
│
├─ Reason 4: Blood group mismatch
│  │
│  └─ SOS wants: O+
│     Donors have: A+, B+, AB+
│     │
│     └─ ❌ Create donor with O+ blood group
│
├─ Reason 5: VEINLINE_CITY_MATCH_STRICT = False
│  │
│  └─ This might cause issues with blank cities
│     Check settings.py: VEINLINE_CITY_MATCH_STRICT
│     │
│     ├─ If False → Set to True
│     └─ If True → Continue below
│
└─ Still no match? → Debug in Django shell:
   │
   from sos.services import match_donors_for_request
   from sos.models import SOSRequest
   
   sos = SOSRequest.objects.first()
   donors = match_donors_for_request(sos)
   print(list(donors))  # See what's returned
```

## 📱 SMS Shows "Skipped" Status?

```
START: SMS result shows "skipped": true
│
├─ Check reason field in result
│
├─ Reason: "missing_api_key"
│  └─ ❌ SMS_API_KEY not set in environment
│     Solution: export SMS_API_KEY=your_key
│
├─ Reason: "invalid_phone"
│  └─ ❌ Phone number format invalid
│     Solution: Use E.164 format +919876543210
│
├─ Reason: "unsupported_provider"
│  └─ ❌ SMS_PROVIDER not set to fast2sms or textlocal
│     Solution: export SMS_PROVIDER=fast2sms
│
├─ Reason: "timeout"
│  └─ ⚠ Network request took >20 seconds
│     Solution: Check internet, try again later
│
├─ Reason: "request_error"
│  └─ ❌ Network/connection error
│     Solution: Check internet connection
│
└─ Reason: "provider_error"
   └─ ❌ SMS provider returned error
      Solution: Check provider API status, verify key
```

## 📊 SMS Shows "ok": false?

```
START: SMS result shows "ok": false
│
├─ This means SMS failed to send (not skipped)
│
├─ Check "reason" field:
│  │
│  ├─ "provider_error" → SMS service returned error
│  │  └─ Check: Fast2SMS or Textlocal dashboard
│  │     - Is account active?
│  │     - Is account balance sufficient?
│  │     - Is API key correct?
│  │
│  ├─ "timeout" → Request took too long
│  │  └─ Solution: Check internet, retry
│  │
│  ├─ "request_error" → Network error
│  │  └─ Solution: Check internet, try again
│  │
│  └─ "unexpected_error" → Unknown error
│     └─ Check: Django logs for exception details
```

## 🆚 Different Output? Check:

```
Test Script Output:
- "✓ SMS sent successfully" → ✅ Good!
- "⚠ SMS skipped: ..." → ⚠ Check reason field
- "✗ SMS failed: ..." → ❌ Check error details
- "⚠ {name}: No phone number" → ❌ Add phone_e164 to profile
- "⚠ {name}: No phone number" → ❌ Donor profile incomplete

API Response:
- "sms": {"ok": true} → ✅ Sent successfully
- "sms": {"ok": false} → ❌ Check reason field
- "skipped": "No phone number" → ⚠ Donor has no phone
- Missing "sms" field? → ⚠ Donor not notified at all
```

## 🔧 Quick Fixes

| Issue | Quick Fix |
|-------|-----------|
| SMS_API_KEY not found | `export SMS_API_KEY=your_key` |
| SMS_PROVIDER not set | `export SMS_PROVIDER=fast2sms` |
| No donors found | Create donors with `test_sos_sms_workflow.py` |
| City mismatch | Ensure exact city name match (case-sensitive) |
| Phone format wrong | Use E.164: +919876543210 |
| Donor unavailable | Set `is_available=True` in DonorDetails |
| Blood group incompatible | Use compatible blood groups |
| API key invalid | Verify on Fast2SMS/Textlocal dashboard |
| SMS service down | Check provider status page |
| Timeout error | Check internet connection |
| SMS skipped | Check reason field for cause |

## 🚀 If Everything Passes:

```
✅ test_sos_sms_workflow.py shows:
   - SOS Request created: #1
   - Found N matching donors
   - SMS Sent: N/N
   - No errors

✅ Check SMS provider dashboard:
   - SMS delivery status: Delivered/Pending
   - Sender ID matches VEINLN
   - Message content visible

✅ Database check:
   - SOSRequest created
   - SOSResponse records exist
   - channel='sms' for all responses

✅ Next step:
   - Configure .env for production
   - Test with real donor phone numbers
   - Monitor SMS delivery in production
```

## 📞 Getting Help

If you're stuck:

1. **Collect information**
   ```bash
   # SMS settings
   echo "SMS_API_KEY: $SMS_API_KEY"
   echo "SMS_PROVIDER: $SMS_PROVIDER"
   
   # Database info
   python manage.py shell
   from accounts.models import Profile
   from donations.models import DonorDetails
   print("Donors:", Profile.objects.filter(role='donor').count())
   print("With phone:", Profile.objects.filter(role='donor', phone_e164__isnull=False).count())
   ```

2. **Test SMS directly**
   ```bash
   python manage.py shell
   from core.services.sms import send_sms
   result = send_sms('+919876543210', 'Test message')
   print(result)
   ```

3. **Check logs**
   ```bash
   tail -f logs/django.log | grep SMS
   ```

4. **Verify on provider dashboard**
   - Log into Fast2SMS or Textlocal
   - Check SMS history
   - Check account balance
   - Verify API key in settings

## ❓ Still Confused?

**Most Common Issues** (top 3):

1. **SMS_API_KEY not set**
   - Fix: `export SMS_API_KEY=your_key`
   - Verify: `echo $SMS_API_KEY`

2. **No donors created with phone numbers**
   - Fix: Run `python test_sos_sms_workflow.py` (creates test data)
   - Verify: Check database has donors

3. **City name mismatch (case-sensitive)**
   - Fix: Ensure SOS city matches donor city exactly
   - Example: Both "Bangalore" not "bangalore" vs "Bangalore"

---

**Need More Help?**
- Check: [SOS_SMS_SETUP_GUIDE.md](SOS_SMS_SETUP_GUIDE.md)
- Check: [SOS_SMS_QUICK_REFERENCE.md](SOS_SMS_QUICK_REFERENCE.md)
- Check: Django logs for detailed errors
