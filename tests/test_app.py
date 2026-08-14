from copy import deepcopy

import pytest
from fastapi.testclient import TestClient

from src import app as app_module


@pytest.fixture
def client():
    original_activities = deepcopy(app_module.activities)
    with TestClient(app_module.app) as test_client:
        yield test_client
    app_module.activities.clear()
    app_module.activities.update(original_activities)


def test_get_activities_returns_seeded_activities(client):
    response = client.get("/activities")

    assert response.status_code == 200
    data = response.json()
    assert "Chess Club" in data
    assert "participants" in data["Chess Club"]


def test_signup_adds_participant_and_is_visible_in_later_request(client):
    email = "student@mergington.edu"

    response = client.post(
        "/activities/Chess Club/signup",
        params={"email": email},
    )

    assert response.status_code == 200
    assert response.json() == {
        "message": f"Signed up {email} for Chess Club"
    }
    activities = client.get("/activities").json()
    assert activities["Chess Club"]["participants"].count(email) == 1


def test_duplicate_signup_is_rejected_without_mutating_participants(client):
    email = "student@mergington.edu"
    endpoint = "/activities/Chess Club/signup"

    first_response = client.post(endpoint, params={"email": email})
    second_response = client.post(endpoint, params={"email": email})

    assert first_response.status_code == 200
    assert second_response.status_code == 400
    assert second_response.json() == {
        "detail": "Student is already signed up for this activity"
    }
    activities = client.get("/activities").json()
    assert activities["Chess Club"]["participants"].count(email) == 1


def test_signup_for_unknown_activity_returns_404_without_mutating_data(client):
    before = client.get("/activities").json()

    response = client.post(
        "/activities/Unknown/signup",
        params={"email": "student@mergington.edu"},
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Activity not found"}
    assert client.get("/activities").json() == before