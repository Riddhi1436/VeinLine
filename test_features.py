#!/usr/bin/env python
"""Test script to verify all feature links are working"""
import time
import urllib.request
import urllib.error

# Give server time to start
time.sleep(2)

# Feature links to test
feature_links = {
    'Privacy First (Eligibility)': 'http://localhost:8000/eligibility/',
    'Instant Matching (Appointments)': 'http://localhost:8000/appointments/',
    'SMS Alerts (Contact)': 'http://localhost:8000/contact/',
    'Analytics (Donor Dashboard)': 'http://localhost:8000/dashboard/donor/',
    'Privacy Policy': 'http://localhost:8000/privacy/',
    'Terms of Service': 'http://localhost:8000/terms/',
    'Support': 'http://localhost:8000/support/',
    'Home': 'http://localhost:8000/',
}

print("Testing Feature Links")
print("=" * 60)

all_working = True
for name, url in feature_links.items():
    try:
        response = urllib.request.urlopen(url, timeout=5)
        status = response.status
        print(f"✓ {name:40} - Status: {status}")
    except Exception as e:
        print(f"✗ {name:40} - Error: {str(e)[:40]}")
        all_working = False

print("=" * 60)
if all_working:
    print("✓ All features are working!")
else:
    print("✗ Some features have issues")
