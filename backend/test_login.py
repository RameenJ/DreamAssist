#!/usr/bin/env python3
"""
Test login endpoint with user credentials
"""
import asyncio
import aiohttp
import json

async def test_login():
    email = "emanrizwan123@gmail.com"
    password = "Emanrizwan123@"
    
    login_data = {
        "email": email,
        "password": password
    }
    
    print(f"\n🔐 Testing login with:")
    print(f"  Email: {email}")
    print(f"  Password: [REDACTED]")
    print("=" * 60)
    
    try:
        async with aiohttp.ClientSession() as session:
            # Test login endpoint
            async with session.post(
                "http://localhost:8000/auth/login",
                json=login_data,
                headers={"Content-Type": "application/json"}
            ) as response:
                print(f"\n📡 Login Response Status: {response.status}")
                response_data = await response.json()
                
                if response.status == 200:
                    print("✅ Login Successful!")
                    token = response_data.get("access_token")
                    print(f"Token: {token[:50]}...")
                    
                    # Now test /users/me with the token
                    print("\n" + "=" * 60)
                    print("📡 Testing GET /users/me with token...")
                    async with session.get(
                        "http://localhost:8000/users/me",
                        headers={"Authorization": f"Bearer {token}"}
                    ) as me_response:
                        print(f"Response Status: {me_response.status}")
                        me_data = await me_response.json()
                        
                        if me_response.status == 200:
                            print("✅ GET /users/me Successful!")
                            print(json.dumps(me_data, indent=2, default=str))
                        else:
                            print(f"❌ Error: {me_data}")
                else:
                    print(f"❌ Login Failed!")
                    print(json.dumps(response_data, indent=2))
                    
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_login())
