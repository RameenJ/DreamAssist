# Test script to verify diagnostic quiz endpoints
# Run this after starting the backend server

import requests
import json

BASE_URL = "http://localhost:8000"

# First, you need to sign up and login to get a token
def test_signup_and_login():
    """Step 1: Create a user and get auth token"""
    # Signup
    signup_data = {
        "email": "testuser_diagnostic@example.com",
        "password": "TestPass123!",
        "firstname": "Test",
        "lastname": "User",
        "age": 25,
        "university_name": "Test University"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/auth/signup", json=signup_data)
        print(f"Signup: {response.status_code}")
        if response.status_code != 201:
            print(f"Signup failed (might already exist): {response.json()}")
    except Exception as e:
        print(f"Signup error: {e}")
    
    # Login
    login_data = {
        "email": "testuser_diagnostic@example.com",
        "password": "TestPass123!"
    }
    
    response = requests.post(f"{BASE_URL}/auth/login", json=login_data)
    print(f"Login: {response.status_code}")
    
    if response.status_code == 200:
        token = response.json()["access_token"]
        print(f"Token obtained: {token[:20]}...")
        return token
    else:
        print(f"Login failed: {response.json()}")
        return None


def test_generate_quiz(token):
    """Step 2: Generate a diagnostic quiz"""
    headers = {"Authorization": f"Bearer {token}"}
    data = {"subject": "Data Structures"}
    
    response = requests.post(
        f"{BASE_URL}/diagnostic/generate-quiz",
        json=data,
        headers=headers
    )
    
    print(f"\nGenerate Quiz: {response.status_code}")
    if response.status_code == 200:
        quiz_data = response.json()
        print(f"Subject: {quiz_data['subject']}")
        print(f"Number of questions: {len(quiz_data['questions'])}")
        print("\nFirst question:")
        print(f"  Q: {quiz_data['questions'][0]['question']}")
        print(f"  Options: {quiz_data['questions'][0]['options']}")
        return quiz_data
    else:
        print(f"Failed: {response.json()}")
        return None


def test_submit_quiz(token, quiz_data):
    """Step 3: Submit quiz answers"""
    headers = {"Authorization": f"Bearer {token}"}
    
    # Create dummy answers (selecting first option for each question)
    answers = [
        {
            "question": q["question"],
            "user_answer": q["options"][0]
        }
        for q in quiz_data["questions"]
    ]
    
    data = {
        "subject": quiz_data["subject"],
        "answers": answers
    }
    
    response = requests.post(
        f"{BASE_URL}/diagnostic/submit-quiz",
        json=data,
        headers=headers
    )
    
    print(f"\nSubmit Quiz: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print(f"Level: {result['level']}")
        print(f"Study Pace: {result['study_pace']}")
        print(f"Study Style: {result['study_style']}")
        print(f"Break Preference: {result['break_preference']}")
        return result
    else:
        print(f"Failed: {response.json()}")
        return None


def test_manual_level(token):
    """Step 4: Set manual level"""
    headers = {"Authorization": f"Bearer {token}"}
    data = {
        "subject": "Algorithms",
        "level": "intermediate"
    }
    
    response = requests.post(
        f"{BASE_URL}/diagnostic/set-manual-level",
        json=data,
        headers=headers
    )
    
    print(f"\nSet Manual Level: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print(f"Message: {result['message']}")
        print(f"Subject: {result['subject']}")
        print(f"Level: {result['level']}")
        return result
    else:
        print(f"Failed: {response.json()}")
        return None


def test_get_profiles(token):
    """Step 5: Get user's subject profiles"""
    headers = {"Authorization": f"Bearer {token}"}
    
    response = requests.get(
        f"{BASE_URL}/diagnostic/my-profiles",
        headers=headers
    )
    
    print(f"\nGet My Profiles: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        profiles = result["subject_profiles"]
        print(f"Number of profiles: {len(profiles)}")
        for profile in profiles:
            print(f"\n  Subject: {profile['subject']}")
            print(f"  Level: {profile['level']}")
            print(f"  Method: {profile['assessment_method']}")
        return result
    else:
        print(f"Failed: {response.json()}")
        return None


if __name__ == "__main__":
    print("=" * 60)
    print("DIAGNOSTIC QUIZ FEATURE TEST")
    print("=" * 60)
    
    print("\nMake sure backend is running: uvicorn main:app --reload")
    input("Press Enter to start tests...")
    
    # Step 1: Get auth token
    token = test_signup_and_login()
    if not token:
        print("\n❌ Failed to get auth token. Exiting.")
        exit(1)
    
    # Step 2: Generate quiz
    quiz_data = test_generate_quiz(token)
    if not quiz_data:
        print("\n❌ Failed to generate quiz. Exiting.")
        exit(1)
    
    # Step 3: Submit quiz
    quiz_result = test_submit_quiz(token, quiz_data)
    if not quiz_result:
        print("\n❌ Failed to submit quiz. Exiting.")
        exit(1)
    
    # Step 4: Set manual level
    manual_result = test_manual_level(token)
    if not manual_result:
        print("\n⚠️  Manual level setting failed.")
    
    # Step 5: Get all profiles
    profiles = test_get_profiles(token)
    
    print("\n" + "=" * 60)
    print("✅ ALL TESTS COMPLETED!")
    print("=" * 60)
