#!/usr/bin/env python
"""
VeinLine Google OAuth Setup Verification Script
Checks that all required configurations are in place for Google authentication.
"""

import os
import sys
import django
from pathlib import Path

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'veinline_backend.settings')
sys.path.insert(0, str(Path(__file__).parent))

django.setup()

from django.conf import settings
from django.contrib.sites.models import Site
from allauth.socialaccount.models import SocialApp
from django.contrib.auth.models import User

def check_django_settings():
    """Check Django settings are properly configured."""
    print("\n📋 Checking Django Settings...")
    checks = []
    
    # Check SITE_ID
    if settings.SITE_ID:
        print(f"  ✓ SITE_ID is set to {settings.SITE_ID}")
        checks.append(True)
    else:
        print("  ✗ SITE_ID not configured")
        checks.append(False)
    
    # Check allauth in INSTALLED_APPS
    required_apps = [
        'allauth',
        'allauth.account',
        'allauth.socialaccount',
        'allauth.socialaccount.providers.google'
    ]
    for app in required_apps:
        if app in settings.INSTALLED_APPS:
            print(f"  ✓ {app} in INSTALLED_APPS")
            checks.append(True)
        else:
            print(f"  ✗ {app} NOT in INSTALLED_APPS")
            checks.append(False)
    
    # Check authentication backends
    if 'allauth.account.auth_backends.AuthenticationBackend' in settings.AUTHENTICATION_BACKENDS:
        print(f"  ✓ AllAuth authentication backend configured")
        checks.append(True)
    else:
        print(f"  ✗ AllAuth authentication backend NOT configured")
        checks.append(False)
    
    return all(checks)

def check_env_variables():
    """Check environment variables."""
    print("\n🔑 Checking Environment Variables...")
    checks = []
    
    client_id = os.getenv('GOOGLE_OAUTH_CLIENT_ID', '')
    client_secret = os.getenv('GOOGLE_OAUTH_CLIENT_SECRET', '')
    
    if client_id and client_id != '':
        print(f"  ✓ GOOGLE_OAUTH_CLIENT_ID is set")
        checks.append(True)
    else:
        print(f"  ✗ GOOGLE_OAUTH_CLIENT_ID is NOT set (required for Google OAuth)")
        checks.append(False)
    
    if client_secret and client_secret != '':
        print(f"  ✓ GOOGLE_OAUTH_CLIENT_SECRET is set")
        checks.append(True)
    else:
        print(f"  ✗ GOOGLE_OAUTH_CLIENT_SECRET is NOT set (required for Google OAuth)")
        checks.append(False)
    
    return all(checks)

def check_database_setup():
    """Check database is properly set up."""
    print("\n🗄️  Checking Database Setup...")
    checks = []
    
    try:
        # Check if Site exists
        site = Site.objects.get(id=settings.SITE_ID)
        print(f"  ✓ Site found: {site.domain}")
        checks.append(True)
    except Site.DoesNotExist:
        print(f"  ✗ Site with ID {settings.SITE_ID} does not exist")
        checks.append(False)
    
    # Check if Google OAuth app is configured
    try:
        google_app = SocialApp.objects.get(provider='google')
        print(f"  ✓ Google OAuth app configured in database")
        if google_app.client_id:
            print(f"    - Client ID: {google_app.client_id[:20]}...")
        checks.append(True)
    except SocialApp.DoesNotExist:
        print(f"  ⚠️  Google OAuth app NOT configured in database")
        print(f"    You'll need to add it via Django admin after setting env vars")
        checks.append(False)
    
    return len(checks) > 0

def check_templates():
    """Check if login template has Google OAuth button."""
    print("\n📄 Checking Templates...")
    checks = []
    
    login_template = Path(__file__).parent / 'templates' / 'auth' / 'login.html'
    if login_template.exists():
        content = login_template.read_text()
        if 'provider_login_url' in content and 'google' in content:
            print(f"  ✓ Login template has Google OAuth button")
            checks.append(True)
        elif 'google_login' in content:
            print(f"  ⚠️  Login template uses old 'google_login' URL (needs fixing)")
            checks.append(False)
        else:
            print(f"  ✗ Login template missing Google OAuth button")
            checks.append(False)
    else:
        print(f"  ✗ Login template not found at {login_template}")
        checks.append(False)
    
    return any(checks)

def check_models():
    """Check if Profile model exists for user profiles."""
    print("\n👤 Checking User Profile Setup...")
    checks = []
    
    try:
        from accounts.models import Profile, UserRole
        print(f"  ✓ Profile model found")
        print(f"  ✓ User roles available: {', '.join([role[0] for role in UserRole.choices])}")
        checks.append(True)
    except ImportError:
        print(f"  ✗ Profile model not found")
        checks.append(False)
    
    return all(checks)

def print_next_steps():
    """Print next steps for setting up Google OAuth."""
    print("\n" + "="*60)
    print("📍 NEXT STEPS FOR GOOGLE OAUTH SETUP")
    print("="*60)
    
    print("""
1. CREATE GOOGLE OAUTH CREDENTIALS:
   - Go to https://console.cloud.google.com/
   - Create a new project or select existing one
   - Go to APIs & Services > Credentials
   - Click "Create Credentials" > "OAuth client ID"
   - Configure OAuth consent screen if needed (choose "External")
   - Create Web application credentials with:
     * Authorized JavaScript origins: http://127.0.0.1:8000
     * Authorized redirect URIs: http://127.0.0.1:8000/accounts/google/login/callback/

2. UPDATE .env FILE:
   - Open .env in the project root
   - Add your credentials:
     GOOGLE_OAUTH_CLIENT_ID=your_client_id_here
     GOOGLE_OAUTH_CLIENT_SECRET=your_client_secret_here
   - Save and restart the server

3. CONFIGURE IN DJANGO ADMIN:
   - Start the server: start_server.bat (Windows) or ./start_server.sh (Linux/Mac)
   - Go to http://127.0.0.1:8000/admin/
   - Log in with your admin account
   - Navigate to Social applications
   - Click "Add Social application"
   - Fill in:
     * Provider: Google
     * Name: Google OAuth
     * Client id: (from Google Console)
     * Secret key: (from Google Console)
     * Sites: Select your site
   - Save

4. TEST GOOGLE LOGIN:
   - Go to http://127.0.0.1:8000/login/
   - Click "Continue with Google"
   - Sign in with your Google account
   - You should be redirected to the home page

For production:
   - Update OAuth redirect URIs to your production domain
   - Publish OAuth consent screen for public use
   - Update ALLOWED_HOSTS in settings
""")

def main():
    """Run all checks."""
    print("\n" + "="*60)
    print("🔍 VEINLINE GOOGLE OAUTH SETUP VERIFICATION")
    print("="*60)
    
    results = {
        "Django Settings": check_django_settings(),
        "Environment Variables": check_env_variables(),
        "Templates": check_templates(),
        "User Profile Setup": check_models(),
        "Database Setup": check_database_setup(),
    }
    
    print("\n" + "="*60)
    print("✅ VERIFICATION SUMMARY")
    print("="*60)
    
    for check, passed in results.items():
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status}: {check}")
    
    print_next_steps()
    
    # Return exit code
    all_passed = all(results.values())
    return 0 if all_passed else 1

if __name__ == '__main__':
    try:
        sys.exit(main())
    except Exception as e:
        print(f"\n❌ Error during verification: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
