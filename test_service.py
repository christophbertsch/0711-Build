#!/usr/bin/env python3
"""
Simple test script to verify the OpenHands Runner service
"""
import asyncio
import httpx
import json
import time

BASE_URL = "http://localhost:8080"

async def test_service():
    """Test the service endpoints"""
    async with httpx.AsyncClient(timeout=30) as client:
        print("🔍 Testing OpenHands Runner Service")
        print("=" * 50)
        
        # Test health endpoint
        print("1. Testing health endpoint...")
        try:
            response = await client.get(f"{BASE_URL}/health")
            print(f"   Status: {response.status_code}")
            print(f"   Response: {response.json()}")
        except Exception as e:
            print(f"   Error: {e}")
        
        print()
        
        # Test create run endpoint
        print("2. Testing create run endpoint...")
        run_data = {
            "project_id": "test-project",
            "compiled_prompt": "Create a simple Python hello world script",
            "repository": None,
            "metadata": {"test": True, "source": "test_script"}
        }
        
        try:
            response = await client.post(
                f"{BASE_URL}/runs",
                json=run_data,
                headers={"Content-Type": "application/json"}
            )
            print(f"   Status: {response.status_code}")
            if response.status_code == 200:
                run_response = response.json()
                print(f"   Response: {run_response}")
                run_id = run_response.get("run_id")
                
                if run_id:
                    # Test get run endpoint
                    print()
                    print("3. Testing get run endpoint...")
                    await asyncio.sleep(2)  # Wait a bit
                    
                    get_response = await client.get(f"{BASE_URL}/runs/{run_id}")
                    print(f"   Status: {get_response.status_code}")
                    print(f"   Response: {get_response.json()}")
                    
                    # Test get run detail endpoint
                    print()
                    print("4. Testing get run detail endpoint...")
                    detail_response = await client.get(f"{BASE_URL}/runs/{run_id}/detail")
                    print(f"   Status: {detail_response.status_code}")
                    if detail_response.status_code == 200:
                        detail_data = detail_response.json()
                        print(f"   Run ID: {detail_data.get('run_id')}")
                        print(f"   Status: {detail_data.get('status')}")
                        print(f"   Percent: {detail_data.get('percent')}")
                        print(f"   Artifacts: {len(detail_data.get('artifacts', []))}")
            else:
                print(f"   Error: {response.text}")
        except Exception as e:
            print(f"   Error: {e}")
        
        print()
        
        # Test list runs endpoint
        print("5. Testing list runs endpoint...")
        try:
            response = await client.get(f"{BASE_URL}/runs")
            print(f"   Status: {response.status_code}")
            if response.status_code == 200:
                runs = response.json()
                print(f"   Total runs: {len(runs)}")
                if runs:
                    print(f"   Latest run: {runs[0]['run_id']} ({runs[0]['status']})")
        except Exception as e:
            print(f"   Error: {e}")
        
        print()
        print("✅ Test completed!")

if __name__ == "__main__":
    print("Make sure the service is running on http://localhost:8080")
    print("You can start it with: python run.py")
    print()
    
    try:
        asyncio.run(test_service())
    except KeyboardInterrupt:
        print("\n❌ Test interrupted by user")