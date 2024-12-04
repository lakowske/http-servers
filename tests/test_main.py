from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_partial_config_updates():
    """
    Comprehensive test for partial configuration updates

    Verifies ability to update:
    - Top-level configuration
    - Nested configuration
    - Specific nested fields
    """
    test_scenarios = [
        # 1. Update top-level configuration
        {
            "update": {"admin": {"domain": "updated.example.com"}},
            "verify": {"admin": {"domain": "updated.example.com"}},
        },
        # 2. Update nested host configuration
        {
            "update": {
                "container_paths": {
                    "name": "test-container",
                }
            },
            "verify": {
                "container_paths": {
                    "name": "test-container",
                }
            },
        },
        # 3. Update nested podman configuration
        {
            "update": {
                "podman": {
                    "socket_url": "/custom/podman.sock",
                }
            },
            "verify": {
                "podman": {
                    "socket_url": "/custom/podman.sock",
                }
            },
        },
        # 4. Update multiple nested configurations
        {
            "update": {"admin": {"email": "new-admin@example.com"}},
            "verify": {"admin": {"email": "new-admin@example.com"}},
        },
    ]

    for scenario in test_scenarios:
        # Perform partial update
        json_data = scenario["update"]
        patch_response = client.patch("/config", json=json_data)
        assert patch_response.status_code == 200

        # Retrieve updated configuration
        get_response = client.get("/config")
        assert get_response.status_code == 200

        # Verify partial updates
        config = get_response.json()

        def verify_update(expected, actual):
            """Recursively verify configuration updates"""
            for key, value in expected.items():
                if isinstance(value, dict):
                    verify_update(value, actual.get(key, {}))
                else:
                    assert actual.get(key) == value, f"Failed to update {key}"

        verify_update(scenario["verify"], config)

    response = client.get("/config")
    assert response.status_code == 200
