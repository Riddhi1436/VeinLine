import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'veinline_backend.settings')
import django
django.setup()

from donations.models import DonorDetails

print('Total donors:', DonorDetails.objects.count())
print('Available donors:', DonorDetails.objects.filter(is_available=True).count())

for d in DonorDetails.objects.all()[:10]:
    print(d.user_id, d.user.email, d.blood_group, d.city, 'available' if d.is_available else 'not')
