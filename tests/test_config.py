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
            "update": {"domain": "updated.example.com", "debug_mode": True},
            "verify": {"domain": "updated.example.com", "debug_mode": True},
        },
        # 2. Update nested host configuration
        {
            "update": {
                "container": {
                    "host": {"hostname": "test-host", "ip_address": "10.0.0.1"}
                }
            },
            "verify": {
                "container": {
                    "host": {"hostname": "test-host", "ip_address": "10.0.0.1"}
                }
            },
        },
        # 3. Update nested podman configuration
        {
            "update": {
                "container": {
                    "podman": {
                        "socket_path": "/custom/podman.sock",
                        "pull_policy": "never",
                    }
                }
            },
            "verify": {
                "container": {
                    "podman": {
                        "socket_path": "/custom/podman.sock",
                        "pull_policy": "never",
                    }
                }
            },
        },
        # 4. Update multiple nested configurations
        {
            "update": {
                "email": "new-admin@example.com",
                "container": {"max_containers": 25, "host": {"cpu_cores": 16}},
            },
            "verify": {
                "email": "new-admin@example.com",
                "container": {"max_containers": 25, "host": {"cpu_cores": 16}},
            },
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
