#!/usr/bin/env python
"""
Test SOS matching via HTTP API calls
"""
import requests
import json
import time

BASE_URL = 'http://127.0.0.1:8000'

def test_sos_match():
    print("=" * 60)
    print("SOS Match Endpoint Test")
    print("=" * 60)
    
    # Step 1: Register test donor
    print("\n[Step 1] Registering test donor...")
    donor_data = {
        'username': f'test_donor_{int(time.time())}',
        'email': f'donor_{int(time.time())}@test.com',
        'password': 'testpass123',
        'role': 'donor',
        'full_name': 'Test Donor',
        'age': 25,
        'blood_group': 'O+',
        'city': 'Mumbai'
    }
    
    try:
        donor_resp = requests.post(f'{BASE_URL}/api/register/', json=donor_data)
        print(f"Donor registration status: {donor_resp.status_code}")
        if donor_resp.status_code not in [200, 201]:
            print(f"Error: {donor_resp.text}")
            return False
        donor_user = donor_resp.json()
        print(f"✓ Donor created: {donor_data['username']}")
    except Exception as e:
        print(f"✗ Error: {e}")
        return False
    
    # Step 2: Register test patient
    print("\n[Step 2] Registering test patient...")
    patient_data = {
        'username': f'test_patient_{int(time.time())}',
        'email': f'patient_{int(time.time())}@test.com',
        'password': 'testpass123',
        'role': 'patient'
    }
    
    try:
        patient_resp = requests.post(f'{BASE_URL}/api/register/', json=patient_data)
        print(f"Patient registration status: {patient_resp.status_code}")
        if patient_resp.status_code not in [200, 201]:
            print(f"Error: {patient_resp.text}")
            return False
        patient_user = patient_resp.json()
        print(f"✓ Patient created: {patient_data['username']}")
    except Exception as e:
        print(f"✗ Error: {e}")
        return False
    
    # Step 3: Get JWT token for patient
    print("\n[Step 3] Getting JWT token...")
    try:
        token_resp = requests.post(f'{BASE_URL}/api/token/', json={
            'username': patient_data['username'],
            'password': 'testpass123'
        })
        if token_resp.status_code != 200:
            print(f"✗ Token error: {token_resp.status_code}")
            print(f"Response: {token_resp.text}")
            return False
        token = token_resp.json()['access']
        print(f"✓ JWT token obtained")
    except Exception as e:
        print(f"✗ Error: {e}")
        return False
    
    # Step 4: Create SOS request
    print("\n[Step 4] Creating SOS request...")
    sos_data = {
        'blood_group_needed': 'O+',
        'city': 'Mumbai',
        'urgency': 'high',
        'units_needed': 2
    }
    
    try:
        sos_resp = requests.post(f'{BASE_URL}/api/sos/', 
            json=sos_data,
            headers={'Authorization': f'Bearer {token}'}
        )
        if sos_resp.status_code not in [200, 201]:
            print(f"✗ SOS creation error: {sos_resp.status_code}")
            print(f"Response: {sos_resp.text}")
            return False
        sos = sos_resp.json()
        sos_id = sos['id']
        print(f"✓ SOS request created: ID={sos_id}, Blood={sos['blood_group_needed']}, City={sos['city']}")
    except Exception as e:
        print(f"✗ Error: {e}")
        return False
    
    # Step 5: Call match endpoint
    print("\n[Step 5] Calling SOS match endpoint...")
    try:
        match_resp = requests.post(f'{BASE_URL}/api/sos/{sos_id}/match/',
            headers={'Authorization': f'Bearer {token}'}
        )
        print(f"Match response status: {match_resp.status_code}")
        
        if match_resp.status_code == 200:
            result = match_resp.json()
            print(f"\n✓ Match endpoint succeeded!")
            print(json.dumps(result, indent=2))
            print(f"\n  Summary:")
            print(f"  - Matched donors: {result.get('matched_donors', 0)}")
            print(f"  - Responses created: {len(result.get('responses_created_or_found', []))}")
            return True
        else:
            print(f"✗ Match failed with {match_resp.status_code}")
            print(f"Response: {match_resp.text}")
            return False
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    print("Waiting for server to be ready...")
    time.sleep(2)
    success = test_sos_match()
    print("\n" + "=" * 60)
    if success:
        print("TEST PASSED ✓")
    else:
        print("TEST FAILED ✗")
    print("=" * 60)
