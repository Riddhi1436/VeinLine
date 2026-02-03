import os
import sys
from pathlib import Path
import django
from types import SimpleNamespace

# Ensure project root is on sys.path when running this script from scripts/
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'veinline_backend.settings')
django.setup()

from sos.services import match_donors_for_request

# Adjust these values to match sample data in your DB
req = SimpleNamespace(blood_group_needed='A+', city='Mumbai', area='')

donors = match_donors_for_request(req, limit=20)
print('Matched donors count:', donors.count() if hasattr(donors, 'count') else len(donors))
for d in donors:
    user = getattr(d, 'user', None)
    print(f"donor_id={d.user_id}, email={getattr(user,'email','')}, group={d.blood_group}, city={d.city}")

print('Done')
