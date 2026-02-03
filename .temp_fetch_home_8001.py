import requests
r = requests.get('http://127.0.0.1:8001', timeout=5)
print('STATUS', r.status_code)
print('HEADERS:')
for k,v in r.headers.items():
    print(f"{k}: {v}")
print('\nBODY START:\n')
print(r.text[:2000])
