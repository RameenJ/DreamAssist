"""
Test Suite for Scheduler Functions
Tests priority scoring, mood adjustments, and task generation
"""
from datetime import date, datetime, timedelta
from services.planner_engine import PriorityScorer
from services.study_scheduler import DailyScheduler
from models.planner_schemas import StudyTask
from bson import ObjectId

print("\n" + "="*80)
print("SCHEDULER FUNCTIONALITY TESTS")
print("="*80)

# Test 1: Priority Scoring
print("\n📊 TEST 1: Priority Scoring with Moods")
print("-" * 80)
scorer = PriorityScorer()
test_date = date.today()

task = StudyTask(
    id=ObjectId(),
    plan_id=ObjectId(),
    subject="DSA",
    topic="Sorting Algorithms",
    task_type="revise",
    difficulty="hard",
    estimated_time_mins=60,
    quiz_score=55.0,
    priority_score=0.0,
    deadline=test_date + timedelta(days=3),
    status="pending",
    created_at=datetime.utcnow(),
    updated_at=datetime.utcnow()
)

score_neutral = scorer.score_task(task, test_date, "neutral")
score_stressed = scorer.score_task(task, test_date, "stressed")
score_motivated = scorer.score_task(task, test_date, "motivated")

print(f"✅ Score (neutral mood): {score_neutral:.4f}")
print(f"✅ Score (stressed mood): {score_stressed:.4f} (reduced by {((score_neutral - score_stressed) / score_neutral * 100):.1f}%)")
print(f"✅ Score (motivated mood): {score_motivated:.4f} (increased by {((score_motivated - score_neutral) / score_neutral * 100):.1f}%)")

# Verify mood multipliers are applied
if score_stressed < score_neutral:
    print("✅ PASS: Stressed mood correctly reduces priority")
else:
    print("❌ FAIL: Stressed mood should reduce priority")

if score_motivated > score_neutral:
    print("✅ PASS: Motivated mood correctly increases priority")
else:
    print("❌ FAIL: Motivated mood should increase priority")

# Test 2: Task Type Boost
print("\n📋 TEST 2: Task Type Boost")
print("-" * 80)
task_learn = task.model_copy(deep=True)
task_learn.task_type = "learn"
task_practice = task.model_copy(deep=True)
task_practice.task_type = "practice"

score_learn = scorer.score_task(task_learn, test_date, "neutral")
score_revise = score_neutral
score_practice = scorer.score_task(task_practice, test_date, "neutral")

print(f"✅ Learn task score: {score_learn:.4f} (neutral boost: 1.0x)")
print(f"✅ Revise task score: {score_revise:.4f} (boost: 1.2x)")
print(f"✅ Practice task score: {score_practice:.4f} (boost: 0.7x)")

if score_revise > score_practice:
    print("✅ PASS: Revise tasks prioritized over practice")
else:
    print("❌ FAIL: Revise tasks should be higher priority than practice")

# Test 3: Duration Adjustment
print("\n⏱️  TEST 3: Mood-Based Duration Adjustment")
print("-" * 80)
scheduler = DailyScheduler(None)

original_duration = 60

stressed_duration = scheduler._adjust_task_duration_by_mood(original_duration, "stressed")
motivated_duration = scheduler._adjust_task_duration_by_mood(original_duration, "motivated")
neutral_duration = scheduler._adjust_task_duration_by_mood(original_duration, "neutral")

print(f"✅ Original duration: {original_duration} mins")
print(f"✅ Stressed mood: {stressed_duration} mins (reduced by {((original_duration - stressed_duration) / original_duration * 100):.1f}%)")
print(f"✅ Motivated mood: {motivated_duration} mins (increased by {((motivated_duration - original_duration) / original_duration * 100):.1f}%)")
print(f"✅ Neutral mood: {neutral_duration} mins (no change)")

if stressed_duration == int(original_duration * 0.65):
    print("✅ PASS: Stressed duration correctly reduced by 35%")
else:
    print(f"❌ FAIL: Expected {int(original_duration * 0.65)}, got {stressed_duration}")

if motivated_duration == int(original_duration * 1.2):
    print("✅ PASS: Motivated duration correctly increased by 20%")
else:
    print(f"❌ FAIL: Expected {int(original_duration * 1.2)}, got {motivated_duration}")

# Test 4: All moods
print("\n🎭 TEST 4: All Mood Duration Adjustments")
print("-" * 80)
moods_test = [
    ("stressed", 0.65),
    ("frustrated", 0.65),
    ("tired", 0.65),
    ("confused", 0.65),
    ("motivated", 1.2),
    ("confident", 1.2),
    ("engaged", 1.2),
    ("bored", 1.0),
    ("neutral", 1.0),
]

for mood, expected_factor in moods_test:
    result = scheduler._adjust_task_duration_by_mood(60, mood)
    expected = int(60 * expected_factor)
    if result == expected:
        print(f"✅ {mood:12} → {result:3} mins (factor: {expected_factor}x)")
    else:
        print(f"❌ {mood:12} → {result:3} mins (expected {expected})")

print("\n" + "="*80)
print("✅ ALL SCHEDULER TESTS COMPLETED")
print("="*80 + "\n")
