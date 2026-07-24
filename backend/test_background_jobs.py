"""
Test Script: Verify APScheduler Background Task Integration

This script helps verify that the background task integration is working correctly.

Usage:
    python test_background_jobs.py

Requirements:
    - Backend server must be running (uvicorn main:app)
    - MongoDB must be running
"""

import requests
import asyncio
import json
from datetime import datetime
from typing import Dict, Any

# Configuration
BASE_URL = "http://localhost:8000"
HEALTH_ENDPOINT = f"{BASE_URL}/api/health"
SCHEDULER_ENDPOINT = f"{BASE_URL}/api/health/scheduler"


class Colors:
    """ANSI color codes for terminal output"""
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    BLUE = "\033[94m"
    RESET = "\033[0m"
    BOLD = "\033[1m"


def print_header(text: str):
    """Print a formatted header"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{text:^60}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.RESET}\n")


def print_success(text: str):
    """Print a success message"""
    print(f"{Colors.GREEN}✅ {text}{Colors.RESET}")


def print_warning(text: str):
    """Print a warning message"""
    print(f"{Colors.YELLOW}⚠️  {text}{Colors.RESET}")


def print_error(text: str):
    """Print an error message"""
    print(f"{Colors.RED}❌ {text}{Colors.RESET}")


def print_info(text: str):
    """Print an info message"""
    print(f"{Colors.BLUE}ℹ️  {text}{Colors.RESET}")


def print_json(data: Dict[str, Any], indent: int = 2):
    """Pretty print JSON data"""
    print(json.dumps(data, indent=indent, default=str))


async def test_api_health() -> bool:
    """Test basic API health endpoint"""
    print_info("Testing API health endpoint...")
    try:
        response = requests.get(HEALTH_ENDPOINT, timeout=5)
        response.raise_for_status()
        
        data = response.json()
        print_success("API health endpoint responding")
        print(f"  API Status: {data.get('api')}")
        print(f"  Database Status: {data.get('database')}")
        print(f"  Scheduler Status: {data.get('scheduler')}")
        print(f"  Active Jobs: {data.get('jobs')}")
        
        if data.get("database") == "connected":
            print_success("Database connection verified")
        else:
            print_error(f"Database connection issue: {data.get('database')}")
            return False
        
        return True
    except requests.exceptions.ConnectionError:
        print_error("Cannot connect to backend at http://localhost:8000")
        print_info("Make sure the backend is running: uvicorn main:app")
        return False
    except Exception as e:
        print_error(f"API health check failed: {e}")
        return False


async def test_scheduler_status() -> bool:
    """Test scheduler status endpoint"""
    print_info("Testing scheduler status endpoint...")
    try:
        response = requests.get(SCHEDULER_ENDPOINT, timeout=5)
        response.raise_for_status()
        
        data = response.json()
        status = data.get("status")
        jobs = data.get("jobs", [])
        
        print_success("Scheduler status endpoint responding")
        print(f"  Scheduler Status: {status}")
        print(f"  Total Jobs: {len(jobs)}")
        
        if status == "running":
            print_success("Scheduler is RUNNING")
        else:
            print_warning(f"Scheduler status: {status}")
        
        if len(jobs) > 0:
            print_success(f"Found {len(jobs)} scheduled job(s):")
            for job in jobs:
                print(f"    • {job.get('name')}")
                print(f"      ID: {job.get('id')}")
                print(f"      Trigger: {job.get('trigger')}")
                print(f"      Next Run: {job.get('next_run_time')}")
        else:
            print_warning("No jobs found in scheduler")
            return False
        
        return True
    except Exception as e:
        print_error(f"Scheduler status check failed: {e}")
        return False


async def test_adaptive_update_job() -> bool:
    """Verify the daily adaptive update job is configured"""
    print_info("Verifying adaptive update job configuration...")
    try:
        response = requests.get(SCHEDULER_ENDPOINT, timeout=5)
        response.raise_for_status()
        
        data = response.json()
        jobs = data.get("jobs", [])
        
        adaptive_job = None
        for job in jobs:
            if job.get("id") == "adaptive_update_job":
                adaptive_job = job
                break
        
        if adaptive_job is None:
            print_error("Adaptive update job not found in scheduler")
            return False
        
        print_success("Adaptive update job is configured")
        print(f"  Job Name: {adaptive_job.get('name')}")
        print(f"  Trigger: {adaptive_job.get('trigger')}")
        print(f"  Next Execution: {adaptive_job.get('next_run_time')}")
        
        # Parse next run time
        next_run = adaptive_job.get("next_run_time")
        if next_run:
            print_info(f"Job will run at: {next_run}")
        
        return True
    except Exception as e:
        print_error(f"Adaptive job verification failed: {e}")
        return False


async def run_all_tests():
    """Run all tests"""
    print_header("DreamAssist Background Jobs Verification")
    
    print(f"Timestamp: {datetime.now().isoformat()}")
    print(f"Backend URL: {BASE_URL}")
    
    results = []
    
    # Test 1: API Health
    print("\n" + "─"*60)
    print("TEST 1: API Health Check")
    print("─"*60)
    results.append(("API Health", await test_api_health()))
    
    # Test 2: Scheduler Status
    print("\n" + "─"*60)
    print("TEST 2: Scheduler Status")
    print("─"*60)
    results.append(("Scheduler Status", await test_scheduler_status()))
    
    # Test 3: Adaptive Update Job
    print("\n" + "─"*60)
    print("TEST 3: Adaptive Update Job Configuration")
    print("─"*60)
    results.append(("Adaptive Update Job", await test_adaptive_update_job()))
    
    # Summary
    print("\n" + "="*60)
    print_header("Test Summary")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = f"{Colors.GREEN}✅ PASS{Colors.RESET}" if result else f"{Colors.RED}❌ FAIL{Colors.RESET}"
        print(f"  {test_name:.<40} {status}")
    
    print(f"\nResults: {Colors.GREEN}{passed}/{total} passed{Colors.RESET}")
    
    if passed == total:
        print_success("All tests passed! Background jobs are configured correctly.")
        print_info("The adaptive update job will run daily at midnight UTC.")
        return True
    else:
        print_error(f"Some tests failed. Please check the setup.")
        return False


def main():
    """Main entry point"""
    print(f"{Colors.BOLD}DreamAssist Background Jobs Test Suite{Colors.RESET}")
    print(f"Python {__import__('sys').version}")
    
    try:
        success = asyncio.run(run_all_tests())
        exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n" + Colors.YELLOW + "Test interrupted by user" + Colors.RESET)
        exit(1)
    except Exception as e:
        print_error(f"Unexpected error: {e}")
        exit(1)


if __name__ == "__main__":
    main()
