#!/usr/bin/env python3
"""
Test if we can use API directly instead of browser automation
"""
import asyncio
import httpx
import json

USERNAME = "7985531737"
PASSWORD = "rahul123"
BASE_URL = "https://bdgwina.cc"
API_URL = "https://api.bdg88zf.com"  # From the HTML config

async def test_api_login():
    print("=" * 70)
    print("  TESTING API LOGIN")
    print("=" * 70)
    print()
    
    async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
        # Try to login via API
        print("🔐 Attempting API login...")
        
        # Common API endpoints for login
        login_endpoints = [
            f"{API_URL}/api/user/login",
            f"{API_URL}/api/auth/login",
            f"{API_URL}/api/login",
            f"{BASE_URL}/api/user/login",
            f"{BASE_URL}/api/auth/login",
        ]
        
        login_data = {
            "username": USERNAME,
            "phone": USERNAME,
            "account": USERNAME,
            "password": PASSWORD,
        }
        
        for endpoint in login_endpoints:
            try:
                print(f"\n📍 Trying: {endpoint}")
                response = await client.post(
                    endpoint,
                    json=login_data,
                    headers={
                        "Content-Type": "application/json",
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                    }
                )
                
                print(f"   Status: {response.status_code}")
                
                if response.status_code == 200:
                    data = response.json()
                    print(f"   Response: {json.dumps(data, indent=2)[:500]}")
                    
                    if data.get("code") == 0 or data.get("success") or data.get("token"):
                        print("\n✅ LOGIN SUCCESSFUL!")
                        
                        # Try to get game data
                        token = data.get("data", {}).get("token") or data.get("token")
                        if token:
                            print(f"\n🎮 Got token, trying to fetch game data...")
                            
                            game_endpoints = [
                                f"{API_URL}/api/webapi/GetNoaverageEmerdList",
                                f"{API_URL}/api/game/history",
                                f"{API_URL}/api/lottery/history",
                            ]
                            
                            for game_endpoint in game_endpoints:
                                try:
                                    print(f"\n📍 Trying: {game_endpoint}")
                                    game_response = await client.get(
                                        game_endpoint,
                                        headers={
                                            "Authorization": f"Bearer {token}",
                                            "token": token,
                                        },
                                        params={"gameCode": "WinGo_30S", "lottery": "WinGo"}
                                    )
                                    
                                    if game_response.status_code == 200:
                                        game_data = game_response.json()
                                        print(f"   ✅ Got game data!")
                                        print(f"   {json.dumps(game_data, indent=2)[:1000]}")
                                        return
                                        
                                except Exception as e:
                                    print(f"   ❌ Error: {e}")
                        
                        return
                    
            except Exception as e:
                print(f"   ❌ Error: {e}")
        
        print("\n❌ Could not find working API endpoint")
        print("\n💡 The website likely uses session-based auth, not API tokens")
        print("💡 We need to fix the browser automation login")

if __name__ == "__main__":
    asyncio.run(test_api_login())
