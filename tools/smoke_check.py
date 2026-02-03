import os
import sys

# Ensure project root is on path
ROOT = os.path.dirname(os.path.dirname(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'veinline_backend.settings')
import django
from django.test import Client

django.setup()

client = Client()
from django.conf import settings
try:
    # allow testserver host for test client
    ah = list(getattr(settings, 'ALLOWED_HOSTS', []))
    if 'testserver' not in ah:
        ah.append('testserver')
    if '127.0.0.1' not in ah:
        ah.append('127.0.0.1')
    settings.ALLOWED_HOSTS = ah
except Exception:
    pass

urls = ['/', '/sos/create/', '/admin/']

for u in urls:
    try:
        r = client.get(u)
        content = r.content.decode('utf-8', errors='replace')
        snippet = content.strip().replace('\n', ' ')[:250]
        print(f"{u} -> status={r.status_code}, length={len(content)}")
        print("snippet:", snippet)
        print('-' * 80)
    except Exception as e:
        print(f"{u} -> ERROR: {e}")
        import traceback
        traceback.print_exc()
