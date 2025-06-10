"""
System health verification tests - READ ONLY

These tests verify that your running system is healthy without making any changes.
Safe to run against your operational system at any time.
"""

import os
import subprocess
from pathlib import Path

import pytest

from configuration.container import ServerContainer
from services.httpd_service import DEFAULT_HTTPD_CONTAINER_NAME
from services.mail_service import DEFAULT_MAIL_CONTAINER_NAME


@pytest.mark.verification
class TestBasicSystemHealth:
    """Basic system health checks - completely safe"""

    def test_workspace_structure_exists(self):
        """✅ Verify basic workspace structure is intact"""
        workspace = Path(__file__).parent.parent.parent

        # Check key directories exist
        assert (workspace / "actions").exists(), "actions/ directory missing"
        assert (workspace / "configuration").exists(), "configuration/ directory missing"
        assert (workspace / "services").exists(), "services/ directory missing"
        assert (workspace / "templates").exists(), "templates/ directory missing"

        # Check key files exist
        assert (workspace / "actions" / "build.py").exists(), "build.py missing"
        assert (workspace / "requirements.txt").exists(), "requirements.txt missing"

    def test_config_file_exists_and_readable(self):
        """✅ Verify config file exists and is readable"""
        config_path = Path(__file__).parent.parent.parent / "secrets" / "config.yaml"

        assert config_path.exists(), "secrets/config.yaml not found"
        assert config_path.is_file(), "config.yaml is not a file"
        assert os.access(config_path, os.R_OK), "config.yaml is not readable"

    def test_config_loads_successfully(self):
        """✅ Verify configuration loads without errors"""
        container = ServerContainer()
        config_service = container.config_service()

        # This should not raise any exceptions
        config_service.load_yaml_config("secrets/config.yaml")

        # Basic config validation
        assert config_service.config.admin.domain, "Domain not configured"
        assert config_service.config.admin.email, "Email not configured"

    def test_build_directory_accessible(self):
        """✅ Verify build directory is accessible"""
        container = ServerContainer()
        config_service = container.config_service()
        config_service.load_yaml_config("secrets/config.yaml")

        build_root = config_service.config.build.build_root
        build_path = Path(build_root)

        # Should be able to access build directory
        expected_msg = f"Build path {build_root} not accessible"
        assert build_path.exists() or build_path.parent.exists(), expected_msg


@pytest.mark.verification
class TestContainerStatus:
    """Container status verification - READ ONLY"""

    def test_can_list_containers(self):
        """✅ Verify we can query container status"""
        container = ServerContainer()
        podman_service = container.podman_service()

        try:
            containers = podman_service.list_containers()
            # Just verify we can list them - don't require any specific containers
            assert isinstance(containers, list), "Container list should be a list"
        except Exception as exc:  # pylint: disable=broad-except
            pytest.skip(f"Cannot connect to Podman: {exc}")

    def test_httpd_container_status(self):
        """✅ Check HTTP container status if it exists"""
        container = ServerContainer()
        httpd_service = container.httpd_service()

        try:
            container_id = httpd_service.get_container_id(DEFAULT_HTTPD_CONTAINER_NAME)
            if container_id:
                # Container exists - check if it's running
                is_running = httpd_service.is_container_running(container_id)
                # We just verify we can check status - don't require it to be running
                assert isinstance(is_running, bool), "Running status should be boolean"
            else:
                pytest.skip("HTTP container not found - this is OK")
        except Exception as exc:  # pylint: disable=broad-except
            pytest.skip(f"Cannot check HTTP container: {exc}")

    def test_mail_container_status(self):
        """✅ Check mail container status if it exists"""
        container = ServerContainer()
        mail_service = container.mail_service()

        try:
            container_id = mail_service.get_container_id(DEFAULT_MAIL_CONTAINER_NAME)
            if container_id:
                # Container exists - check if it's running
                is_running = mail_service.is_container_running(container_id)
                assert isinstance(is_running, bool), "Running status should be boolean"
            else:
                pytest.skip("Mail container not found - this is OK")
        except Exception as exc:  # pylint: disable=broad-except
            pytest.skip(f"Cannot check mail container: {exc}")


@pytest.mark.verification
class TestCommandLineInterface:
    """CLI interface verification"""

    def test_build_script_is_executable(self):
        """✅ Verify build.py script can be executed"""
        build_script = Path(__file__).parent.parent.parent / "actions" / "build.py"

        assert build_script.exists(), "build.py not found"

        # Try to run help/list commands (safe, read-only)
        try:
            result = subprocess.run(
                ["python", str(build_script), "list_containers"],
                capture_output=True,
                text=True,
                timeout=30,
                cwd=build_script.parent.parent,
                check=False
            )
            # Command should either succeed or fail gracefully
            expected_msg = f"Unexpected return code: {result.returncode}"
            assert result.returncode in [0, 1], expected_msg
        except subprocess.TimeoutExpired:
            pytest.fail("Command timed out - possible hanging")
        except Exception as exc:  # pylint: disable=broad-except
            pytest.skip(f"Cannot test CLI: {exc}")

    def test_python_environment_has_required_packages(self):
        """✅ Verify key packages are installed"""
        try:
            import yaml  # pylint: disable=import-outside-toplevel
            import pydantic  # pylint: disable=import-outside-toplevel
            import podman  # pylint: disable=import-outside-toplevel
            # Just verify imports work
            assert yaml.__name__ == "yaml"
            assert pydantic.__name__ == "pydantic"
            assert podman.__name__ == "podman"
        except ImportError as exc:
            pytest.fail(f"Required package missing: {exc}")
