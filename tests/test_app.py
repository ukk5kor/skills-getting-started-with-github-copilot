"""
Tests for the High School Management System API
"""
import pytest
from fastapi.testclient import TestClient
import sys
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from app import app, activities


@pytest.fixture
def client():
    """Create a test client for the API"""
    return TestClient(app)


@pytest.fixture(autouse=True)
def reset_activities():
    """Reset activities data before each test"""
    import copy
    from app import activities as app_activities
    
    # Create a deep copy of the original activities state
    original_activities = copy.deepcopy(app_activities)
    
    # Reset to original state before test
    app_activities.clear()
    app_activities.update({
        "Chess Club": {
            "description": "Learn strategies and compete in chess tournaments",
            "schedule": "Fridays, 3:30 PM - 5:00 PM",
            "max_participants": 12,
            "participants": ["michael@mergington.edu", "daniel@mergington.edu"]
        },
        "Programming Class": {
            "description": "Learn programming fundamentals and build software projects",
            "schedule": "Tuesdays and Thursdays, 3:30 PM - 4:30 PM",
            "max_participants": 20,
            "participants": ["emma@mergington.edu", "sophia@mergington.edu"]
        },
        "Gym Class": {
            "description": "Physical education and sports activities",
            "schedule": "Mondays, Wednesdays, Fridays, 2:00 PM - 3:00 PM",
            "max_participants": 30,
            "participants": ["john@mergington.edu", "olivia@mergington.edu"]
        }
    })
    
    yield
    
    # Reset to original state after test
    app_activities.clear()
    app_activities.update(original_activities)


def test_root_redirects_to_index(client):
    """Test that root path redirects to index.html"""
    response = client.get("/", follow_redirects=False)
    assert response.status_code == 307
    assert response.headers["location"] == "/static/index.html"


def test_get_activities(client):
    """Test getting all activities"""
    response = client.get("/activities")
    assert response.status_code == 200
    data = response.json()
    
    # Check that we have activities
    assert len(data) >= 3
    assert "Chess Club" in data
    assert "Programming Class" in data
    assert "Gym Class" in data
    
    # Check activity structure
    chess_club = data["Chess Club"]
    assert "description" in chess_club
    assert "schedule" in chess_club
    assert "max_participants" in chess_club
    assert "participants" in chess_club
    assert isinstance(chess_club["participants"], list)


def test_signup_for_activity(client):
    """Test signing up for an activity"""
    email = "newstudent@mergington.edu"
    activity = "Chess Club"
    
    # Get initial participant count
    initial_response = client.get("/activities")
    initial_participants = len(initial_response.json()[activity]["participants"])
    
    # Sign up
    response = client.post(f"/activities/{activity}/signup?email={email}")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert email in data["message"]
    assert activity in data["message"]
    
    # Verify participant was added
    updated_response = client.get("/activities")
    updated_participants = updated_response.json()[activity]["participants"]
    assert len(updated_participants) == initial_participants + 1
    assert email in updated_participants


def test_signup_duplicate_participant(client):
    """Test that duplicate signups are prevented"""
    email = "michael@mergington.edu"  # Already signed up for Chess Club
    activity = "Chess Club"
    
    # Try to sign up again
    response = client.post(f"/activities/{activity}/signup?email={email}")
    assert response.status_code == 400
    data = response.json()
    assert "detail" in data
    assert "already signed up" in data["detail"].lower()


def test_signup_nonexistent_activity(client):
    """Test signing up for a non-existent activity"""
    email = "student@mergington.edu"
    activity = "Nonexistent Activity"
    
    response = client.post(f"/activities/{activity}/signup?email={email}")
    assert response.status_code == 404
    data = response.json()
    assert "detail" in data
    assert "not found" in data["detail"].lower()


def test_multiple_activities_signup(client):
    """Test that a student can sign up for multiple activities"""
    email = "multistudent@mergington.edu"
    
    # Sign up for Chess Club
    response1 = client.post(f"/activities/Chess Club/signup?email={email}")
    assert response1.status_code == 200
    
    # Sign up for Programming Class
    response2 = client.post(f"/activities/Programming Class/signup?email={email}")
    assert response2.status_code == 200
    
    # Verify both signups
    activities_response = client.get("/activities")
    data = activities_response.json()
    assert email in data["Chess Club"]["participants"]
    assert email in data["Programming Class"]["participants"]


def test_activity_with_special_characters(client):
    """Test signing up for activities with special characters in name"""
    from urllib.parse import quote
    
    # First add an activity with special characters for testing
    activities["Art & Crafts"] = {
        "description": "Creative arts",
        "schedule": "Wednesdays, 3:00 PM",
        "max_participants": 10,
        "participants": []
    }
    
    email = "artist@mergington.edu"
    
    # URL encode the activity name
    activity_name = quote("Art & Crafts")
    
    response = client.post(f"/activities/{activity_name}/signup?email={email}")
    assert response.status_code == 200
    
    # Verify signup
    activities_response = client.get("/activities")
    data = activities_response.json()
    assert email in data["Art & Crafts"]["participants"]
