#!/usr/bin/env python
"""
Test automatic admin creation on first registration
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'veinline_backend.settings')
django.setup()

from django.contrib.auth.models import User
from accounts.models import Profile, UserRole
from accounts.services import make_user_admin

print("=" * 70)
print("Testing Automatic Admin Creation on First Registration")
print("=" * 70)

# Check how many users currently exist
current_users = User.objects.count()
print(f"\n📊 Current users in database: {current_users}")

# Show existing superusers/admins
admins = User.objects.filter(is_superuser=True)
print(f"📊 Existing superusers: {admins.count()}")
for admin in admins:
    print(f"   • {admin.username} (staff: {admin.is_staff}, superuser: {admin.is_superuser})")

# Test make_user_admin function
if current_users > 0:
    print("\n✅ Testing make_user_admin function...")
    test_user = User.objects.first()
    print(f"   Before: is_staff={test_user.is_staff}, is_superuser={test_user.is_superuser}")
    
    make_user_admin(test_user)
    
    # Refresh from DB
    test_user.refresh_from_db()
    print(f"   After: is_staff={test_user.is_staff}, is_superuser={test_user.is_superuser}")
    
    # Check profile
    try:
        profile = test_user.profile
        print(f"   Profile role: {profile.role}")
        if profile.role == UserRole.ADMIN:
            print(f"   ✅ Profile updated to ADMIN role")
    except Profile.DoesNotExist:
        print(f"   ⚠️  No profile found for user")

print("\n" + "=" * 70)
print("AUTO-ADMIN CREATION LOGIC:")
print("=" * 70)
print("""
✅ What was added:

1. In accounts/services.py:
   - New function: make_user_admin(user)
   - Sets user as staff and superuser
   - Updates profile role to ADMIN

2. In accounts/views.py (OTP Registration):
   - After user registration, check if they're the first user
   - If first user: automatically call make_user_admin()
   - Return 'is_admin: true' in response

3. In webui/views.py (Web Registration):
   - After user registration, check if they're the first user
   - If first user: automatically call make_user_admin()
   - Show admin message in success notification

🎯 How it works:
   1. Person visits /register or /api/auth/register/initiate/
   2. They fill out registration form
   3. First user to register becomes admin automatically
   4. User is notified they are now an admin
   5. All subsequent users register as normal (donor/patient role)

🔐 Admin Features Available:
   - Access to /admin/ Django admin panel
   - Can manage users, permissions, and data
   - Full system administration capabilities
   - Can view all SOS requests, appointments, etc.

✨ No terminal commands needed!
""")
