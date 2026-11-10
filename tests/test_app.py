from copy import deepcopy

import pytest
from fastapi.testclient import TestClient

import src.app as app_module


ACTIVITY = "Basketball Team"
SIGNUP_URL = "/activities/Basketball%20Team/signup"


@pytest.fixture
def client():
    original_activities = deepcopy(app_module.activities)
    app_module.activities = deepcopy(original_activities)

    try:
        with TestClient(app_module.app) as test_client:
            yield test_client
    finally:
        app_module.activities = original_activities


def test_get_activities_returns_activity_data(client):
    # Arrange

    # Act
    response = client.get("/activities")

    # Assert
    assert response.status_code == 200
    assert response.json() == app_module.activities


def test_signup_adds_participant(client):
    # Arrange
    email = "new-student@example.edu"

    # Act
    response = client.post(SIGNUP_URL, params={"email": email})

    # Assert
    assert response.status_code == 200
    assert response.json() == {"message": f"Signed up {email} for {ACTIVITY}"}
    assert email in app_module.activities[ACTIVITY]["participants"]


def test_signup_rejects_duplicate_participant(client):
    # Arrange
    email = "new-student@example.edu"
    app_module.activities[ACTIVITY]["participants"].append(email)

    # Act
    response = client.post(SIGNUP_URL, params={"email": email})

    # Assert
    assert response.status_code == 400
    assert response.json()["detail"] == "Student already signed up for this activity"
    assert app_module.activities[ACTIVITY]["participants"].count(email) == 1


def test_signup_rejects_full_activity(client):
    # Arrange
    email = "new-student@example.edu"
    app_module.activities[ACTIVITY]["participants"] = ["existing-student@example.edu"]
    app_module.activities[ACTIVITY]["max_participants"] = 1

    # Act
    response = client.post(SIGNUP_URL, params={"email": email})

    # Assert
    assert response.status_code == 400
    assert response.json()["detail"] == "Activity is full"
    assert app_module.activities[ACTIVITY]["participants"] == ["existing-student@example.edu"]


def test_signup_rejects_unknown_activity(client):
    # Arrange
    unknown_activity_url = "/activities/Unknown%20Activity/signup"

    # Act
    response = client.post(
        unknown_activity_url,
        params={"email": "student@example.edu"},
    )

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_signup_requires_email(client):
    # Arrange

    # Act
    response = client.post(SIGNUP_URL)

    # Assert
    assert response.status_code == 422


def test_unregister_removes_participant(client):
    # Arrange
    email = "new-student@example.edu"
    app_module.activities[ACTIVITY]["participants"].append(email)

    # Act
    response = client.delete(SIGNUP_URL, params={"email": email})

    # Assert
    assert response.status_code == 200
    assert response.json() == {"message": f"Removed {email} from {ACTIVITY}"}
    assert email not in app_module.activities[ACTIVITY]["participants"]


def test_unregister_rejects_unknown_participant(client):
    # Arrange
    email = "not-enrolled@example.edu"

    # Act
    response = client.delete(
        SIGNUP_URL,
        params={"email": email},
    )

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Student is not signed up for this activity"


def test_unregister_rejects_unknown_activity(client):
    # Arrange
    unknown_activity_url = "/activities/Unknown%20Activity/signup"

    # Act
    response = client.delete(
        unknown_activity_url,
        params={"email": "student@example.edu"},
    )

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_unregister_requires_email(client):
    # Arrange

    # Act
    response = client.delete(SIGNUP_URL)

    # Assert
    assert response.status_code == 422