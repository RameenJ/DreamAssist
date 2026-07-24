"""
Test: Plan ID Consistency and Retrieval
Verifies that:
1. Plans can be fetched from /plans?status=active
2. The returned plan ID can be used to fetch individual plans
3. No 404 errors occur for valid IDs
4. Only one plan has status='active' per user
"""

import asyncio
import httpx
import json
from typing import Optional

BASE_URL = "http://localhost:8000/api/v1"

class PlanAPITester:
    def __init__(self, base_url: str = BASE_URL):
        self.base_url = base_url
        self.token: Optional[str] = None
        
    async def login(self, email: str, password: str) -> bool:
        """Login and get auth token"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/auth/login",
                json={"email": email, "password": password}
            )
            if response.status_code == 200:
                data = response.json()
                self.token = data.get("access_token")
                print(f"✓ Logged in successfully. Token: {self.token[:20]}...")
                return True
            else:
                print(f"❌ Login failed: {response.status_code}")
                print(f"   Response: {response.text}")
                return False
    
    def _get_headers(self) -> dict:
        """Get headers with auth token"""
        return {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
    
    async def test_list_plans(self, status: str = "active") -> list:
        """Test GET /plans?status=active"""
        print(f"\n📋 Testing: GET /planner/plans?status={status}")
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/planner/plans",
                params={"status_filter": status},
                headers=self._get_headers()
            )
            
            print(f"   Status Code: {response.status_code}")
            
            if response.status_code == 200:
                plans = response.json()
                print(f"   ✓ Found {len(plans)} active plans")
                
                for i, plan in enumerate(plans, 1):
                    plan_id = plan.get("_id") or plan.get("plan_id") or plan.get("id")
                    plan_name = plan.get("plan_name")
                    plan_status = plan.get("status")
                    print(f"     [{i}] ID: {plan_id}")
                    print(f"         Name: {plan_name}")
                    print(f"         Status: {plan_status}")
                
                return plans
            else:
                print(f"   ❌ Failed to list plans")
                print(f"   Response: {response.text}")
                return []
    
    async def test_get_plan(self, plan_id: str) -> Optional[dict]:
        """Test GET /plans/{plan_id}"""
        print(f"\n🔍 Testing: GET /planner/plans/{plan_id}")
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/planner/plans/{plan_id}",
                headers=self._get_headers()
            )
            
            print(f"   Status Code: {response.status_code}")
            
            if response.status_code == 200:
                plan = response.json()
                print(f"   ✓ Plan retrieved successfully")
                print(f"     Name: {plan.get('plan_name')}")
                print(f"     Status: {plan.get('status')}")
                print(f"     Subjects: {plan.get('subjects')}")
                return plan
            elif response.status_code == 404:
                print(f"   ❌ Plan not found (404)")
                print(f"   Response: {response.text}")
                return None
            else:
                print(f"   ❌ Unexpected error ({response.status_code})")
                print(f"   Response: {response.text}")
                return None
    
    async def test_id_consistency(self) -> bool:
        """Test that list plan IDs can be used to fetch individual plans"""
        print("\n" + "="*60)
        print("🧪 TEST: Plan ID Consistency")
        print("="*60)
        
        # Step 1: List plans
        plans = await self.test_list_plans("active")
        
        if not plans:
            print("\n⚠️ No active plans found. Cannot test ID consistency.")
            return False
        
        # Step 2: Use first plan's ID to fetch individual plan
        first_plan = plans[0]
        plan_id = first_plan.get("_id") or first_plan.get("plan_id") or first_plan.get("id")
        
        print(f"\n📌 Using plan ID from list: {plan_id}")
        
        # Step 3: Try to fetch the individual plan
        retrieved_plan = await self.test_get_plan(plan_id)
        
        if retrieved_plan:
            print("\n✅ ID CONSISTENCY CHECK PASSED")
            print(f"   List returned ID: {plan_id}")
            print(f"   Individual fetch succeeded")
            return True
        else:
            print("\n❌ ID CONSISTENCY CHECK FAILED")
            print(f"   Plan ID from list ({plan_id}) could not be fetched individually")
            return False
    
    async def verify_single_active_plan(self) -> bool:
        """Verify only one plan has status='active' per user"""
        print("\n" + "="*60)
        print("🔐 TEST: Single Active Plan Enforcement")
        print("="*60)
        
        plans = await self.test_list_plans("active")
        
        if len(plans) <= 1:
            print(f"\n✅ SINGLE ACTIVE PLAN CHECK PASSED")
            print(f"   User has {len(plans)} active plan(s)")
            return True
        else:
            print(f"\n❌ SINGLE ACTIVE PLAN CHECK FAILED")
            print(f"   User has {len(plans)} active plans (should be max 1)")
            for plan in plans:
                plan_id = plan.get("_id") or plan.get("plan_id") or plan.get("id")
                print(f"     - {plan_id}: {plan.get('plan_name')}")
            return False


async def run_tests(email: str = "test@example.com", password: str = "password123"):
    """Run all tests"""
    tester = PlanAPITester()
    
    # Step 1: Login
    if not await tester.login(email, password):
        print("\n❌ Cannot proceed without authentication")
        return
    
    # Step 2: Test ID consistency
    consistency_passed = await tester.test_id_consistency()
    
    # Step 3: Test single active plan
    single_plan_passed = await tester.verify_single_active_plan()
    
    # Summary
    print("\n" + "="*60)
    print("📊 TEST SUMMARY")
    print("="*60)
    print(f"ID Consistency:          {'✅ PASSED' if consistency_passed else '❌ FAILED'}")
    print(f"Single Active Plan:      {'✅ PASSED' if single_plan_passed else '❌ FAILED'}")
    print("="*60)
    
    if consistency_passed and single_plan_passed:
        print("\n🎉 ALL TESTS PASSED!")
    else:
        print("\n⚠️ Some tests failed. Review the output above.")


if __name__ == "__main__":
    # 🔧 UPDATE THESE CREDENTIALS
    TEST_EMAIL = "your-test-email@example.com"
    TEST_PASSWORD = "your-test-password"
    
    print("Plan ID Consistency Test Suite")
    print("=" * 60)
    print(f"API Base URL: {BASE_URL}")
    print(f"Test User: {TEST_EMAIL}")
    print("=" * 60)
    
    asyncio.run(run_tests(TEST_EMAIL, TEST_PASSWORD))
