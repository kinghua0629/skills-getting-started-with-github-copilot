"""
Tests for the High School Management System API
"""

import pytest
from fastapi.testclient import TestClient
import sys
from pathlib import Path

# Add src to path so we can import the app
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from app import app, activities


@pytest.fixture
def client():
    """Create a test client"""
    return TestClient(app)


@pytest.fixture(autouse=True)
def reset_activities():
    """Reset activities data before each test"""
    # Store original state
    original_participants = {
        activity: details["participants"].copy()
        for activity, details in activities.items()
    }
    
    yield
    
    # Restore original state after test
    for activity, details in activities.items():
        details["participants"] = original_participants[activity].copy()


def test_root_redirect(client):
    """Test that root redirects to static/index.html"""
    response = client.get("/", follow_redirects=False)
    assert response.status_code == 307
    assert response.headers["location"] == "/static/index.html"


def test_get_activities(client):
    """Test getting all activities"""
    response = client.get("/activities")
    assert response.status_code == 200
    
    data = response.json()
    assert isinstance(data, dict)
    assert "Basketball Team" in data
    assert "Soccer Club" in data
    assert "Art Club" in data
    
    # Check structure of an activity
    basketball = data["Basketball Team"]
    assert "description" in basketball
    assert "schedule" in basketball
    assert "max_participants" in basketball
    assert "participants" in basketball


def test_signup_for_activity_success(client):
    """Test successfully signing up for an activity"""
    response = client.post(
        "/activities/Basketball%20Team/signup?email=test@mergington.edu"
    )
    assert response.status_code == 200
    
    data = response.json()
    assert "message" in data
    assert "test@mergington.edu" in data["message"]
    assert "Basketball Team" in data["message"]
    
    # Verify student was added
    assert "test@mergington.edu" in activities["Basketball Team"]["participants"]


def test_signup_for_nonexistent_activity(client):
    """Test signing up for an activity that doesn't exist"""
    response = client.post(
        "/activities/Nonexistent%20Activity/signup?email=test@mergington.edu"
    )
    assert response.status_code == 404
    
    data = response.json()
    assert data["detail"] == "Activity not found"


def test_signup_duplicate_registration(client):
    """Test that a student cannot sign up for the same activity twice"""
    email = "duplicate@mergington.edu"
    
    # First signup should succeed
    response1 = client.post(
        f"/activities/Soccer%20Club/signup?email={email}"
    )
    assert response1.status_code == 200
    
    # Second signup should fail
    response2 = client.post(
        f"/activities/Soccer%20Club/signup?email={email}"
    )
    assert response2.status_code == 400
    
    data = response2.json()
    assert data["detail"] == "Student already signed up for this activity"


def test_signup_multiple_activities(client):
    """Test that a student can sign up for multiple different activities"""
    email = "multi@mergington.edu"
    
    # Sign up for first activity
    response1 = client.post(
        f"/activities/Art%20Club/signup?email={email}"
    )
    assert response1.status_code == 200
    
    # Sign up for second activity
    response2 = client.post(
        f"/activities/Drama%20Club/signup?email={email}"
    )
    assert response2.status_code == 200
    
    # Verify student is in both
    assert email in activities["Art Club"]["participants"]
    assert email in activities["Drama Club"]["participants"]


def test_activity_participants_count(client):
    """Test that participant count is accurate"""
    # Get initial state
    response = client.get("/activities")
    initial_data = response.json()
    initial_count = len(initial_data["Math Club"]["participants"])
    
    # Add a participant
    client.post("/activities/Math%20Club/signup?email=newstudent@mergington.edu")
    
    # Check updated count
    response = client.get("/activities")
    updated_data = response.json()
    new_count = len(updated_data["Math Club"]["participants"])
    
    assert new_count == initial_count + 1


def test_signup_with_special_characters_in_email(client):
    """Test signup with various valid email formats"""
    from urllib.parse import quote
    
    test_cases = [
        ("test.user@mergington.edu", "Art Club"),
        ("test_user@mergington.edu", "Drama Club"),
        ("test+tag@mergington.edu", "Math Club")
    ]
    
    for email, activity in test_cases:
        response = client.post(
            f"/activities/{quote(activity)}/signup?email={quote(email)}"
        )
        assert response.status_code == 200
        assert email in activities[activity]["participants"]


def test_all_activities_exist(client):
    """Test that all expected activities are present"""
    expected_activities = [
        "Basketball Team",
        "Soccer Club",
        "Art Club",
        "Drama Club",
        "Debate Team",
        "Math Club",
        "Chess Club",
        "Programming Class",
        "Gym Class"
    ]
    
    response = client.get("/activities")
    data = response.json()
    
    for activity in expected_activities:
        assert activity in data
        assert data[activity]["max_participants"] > 0
