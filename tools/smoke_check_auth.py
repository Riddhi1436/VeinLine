import os
import sys

ROOT = os.path.dirname(os.path.dirname(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'veinline_backend.settings')
import django
from django.test import Client
from django.contrib.auth import get_user_model
from django.db import IntegrityError

django.setup()

User = get_user_model()
from django.conf import settings

# Ensure hosts
ah = list(getattr(settings, 'ALLOWED_HOSTS', []))
for h in ('testserver', '127.0.0.1'):
    if h not in ah:
        ah.append(h)
settings.ALLOWED_HOSTS = ah

# Create users
created = []
users = [
    ('smoke_admin', 'smoke_admin@example.com', 'Password123!', True),
    ('donor_user', 'donor@example.com', 'Password123!', False),
    ('patient_user', 'patient@example.com', 'Password123!', False),
]
for username, email, pwd, is_super in users:
    try:
        u = User.objects.get(username=username)
        print(f'user exists: {username}')
    except User.DoesNotExist:
        if is_super:
            u = User.objects.create_superuser(username=username, email=email, password=pwd)
        else:
            u = User.objects.create_user(username=username, email=email, password=pwd)
        print(f'created user: {username}')
        created.append(username)

# Create profiles if model exists
try:
    from accounts.models import Profile
    for username, email, pwd, is_super in users:
        u = User.objects.get(username=username)
        if not hasattr(u, 'profile'):
            role = 'admin' if u.is_superuser else ('donor' if 'donor' in username else 'patient')
            Profile.objects.create(user=u, role=role, phone_e164='+911234567890', city='TestCity', area='TestArea')
            print(f'created profile for {username} role={role}')
        else:
            print(f'profile exists for {username}')
except Exception as e:
    print('Profile model not available or error creating profiles:', e)

client = Client()

checks = []

# Anonymous checks
for u in ['/', '/sos/create/', '/admin/']:
    r = client.get(u)
    checks.append((u, r.status_code, r.content[:200]))

# Login as admin
if client.login(username='smoke_admin', password='Password123!'):
    print('logged in as smoke_admin')
    for u in ['/admin/', '/admin/sos/sosrequest/']:
        r = client.get(u)
        checks.append((f'admin:{u}', r.status_code, r.content[:200]))
else:
    print('admin login failed')

# Login as patient and fetch create sos
client.logout()
if client.login(username='patient_user', password='Password123!'):
    print('logged in as patient_user')
    r = client.get('/sos/create/')
    checks.append(('/sos/create/ (patient)', r.status_code, r.content[:200]))
else:
    print('patient login failed')

# Print results
for u, status, content in checks:
    snippet = content.decode('utf-8', errors='replace')
    snippet = ' '.join(snippet.split())[:250]
    print(f"{u} -> {status} | snippet: {snippet}")
