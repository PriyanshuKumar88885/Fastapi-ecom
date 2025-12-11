#!/usr/bin/env python3
"""Test script to verify Keycloak integration works."""

from app.keycloak import keycloak_admin

print("Testing Keycloak user creation...")
print("=" * 50)

username = "test_via_script"
password = "password"
role = "tenant_admin"

try:
    result = keycloak_admin.create_user(username, password, role)
    print(f"✅ User creation result: {result}")
    
    if result:
        print(f"\nUser '{username}' created successfully in Keycloak")
        print("Testing if user can login...")
        
        import requests
        token_response = requests.post(
            "http://localhost:8080/realms/ecom/protocol/openid-connect/token",
            data={
                'client_id': 'Confidential-Client',
                'client_secret': 'ecom-secret',
                'username': username,
                'password': password,
                'grant_type': 'password'
            }
        )
        
        if token_response.status_code == 200:
            token = token_response.json().get('access_token')
            if token:
                print(f"✅ SUCCESS! User can login. Token: {token[:50]}...")
            else:
                print(f"❌ Token is null")
                print(token_response.json())
        else:
            print(f"❌ Login failed: {token_response.status_code}")
            print(token_response.json())
    else:
        print(f"User '{username}' already exists")
        
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
