"""
Configuration validation tests - test config parsing without external dependencies.
"""

import os
import tempfile

import pytest
import yaml
from pydantic import ValidationError

from configuration.app import AdminContext, BuildContext, Config
from services.config_service import ConfigService, load_yaml_config, merge_config


@pytest.mark.config
class TestConfigurationLoading:
    """Test configuration loading and validation"""

    def test_minimal_valid_config(self):
        """Test that minimal valid config loads successfully"""
        config_data = {"admin": {"domain": "example.com", "email": "admin@example.com"}}

        # Should not raise any exceptions
        config = Config(**config_data)
        assert config.admin.domain == "example.com"
        assert config.admin.email == "admin@example.com"

    def test_config_with_all_fields(self):
        """Test config loading with all optional fields"""
        config_data = {
            "admin": {
                "domain": "test.example.com",
                "email": "admin@test.example.com",
                "country": "US",
                "state": "California",
                "locality": "San Francisco",
                "organization": "Test Org",
            },
            "imap": {"username": "imap@test.com", "password": "imap_pass"},
            "smtp": {"username": "smtp@test.com", "password": "smtp_pass"},
            "proxies": [
                {"url": "/api", "backend": "http://localhost:3000"},
                {"url": "/app", "backend": "http://localhost:8080"},
            ],
        }

        config = Config(**config_data)
        assert config.admin.domain == "test.example.com"
        assert len(config.proxies) == 2
        assert config.imap.username == "imap@test.com"

    def test_config_validation_errors(self):
        """Test that invalid configs raise validation errors"""
        invalid_configs = [
            {},  # Missing admin section
            {"admin": {}},  # Missing domain and email
            {"admin": {"domain": "test.com"}},  # Missing email
            {"admin": {"email": "test@test.com"}},  # Missing domain
        ]

        for invalid_config in invalid_configs:
            with pytest.raises(ValidationError):
                Config(**invalid_config)

    def test_yaml_config_loading(self):
        """Test loading config from YAML file"""
        config_data = {"admin": {"domain": "yaml.example.com", "email": "admin@yaml.example.com"}}

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump(config_data, f)
            temp_path = f.name

        try:
            loaded_config = load_yaml_config(temp_path)
            assert loaded_config["admin"]["domain"] == "yaml.example.com"
        finally:
            os.unlink(temp_path)

    def test_config_merge_functionality(self):
        """Test configuration merging"""
        base_config = Config(admin=AdminContext(domain="base.com", email="base@base.com"))

        update_data = {
            "admin": {
                "domain": "updated.com"
                # email should remain unchanged
            }
        }

        merged_config = merge_config(base_config, update_data)

        assert merged_config.admin.domain == "updated.com"
        assert merged_config.admin.email == "base@base.com"  # Unchanged

    def test_config_service_initialization(self):
        """Test ConfigService initialization and loading"""
        config = Config(admin=AdminContext(domain="service.com", email="admin@service.com"))

        config_service = ConfigService(config)
        assert config_service.config.admin.domain == "service.com"

    def test_build_context_defaults(self):
        """Test BuildContext uses sensible defaults"""
        build_context = BuildContext()

        assert build_context.build_root == "."  # Actual default
        assert build_context.template_root == "templates"
        assert isinstance(build_context.build_root, str)
        assert isinstance(build_context.template_root, str)


@pytest.mark.config
class TestConfigurationEdgeCases:
    """Test edge cases and error conditions"""

    def test_empty_yaml_file(self):
        """Test handling of empty YAML file"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write("")  # Empty file
            temp_path = f.name

        try:
            result = load_yaml_config(temp_path)
            assert result is None
        finally:
            os.unlink(temp_path)

    def test_invalid_yaml_syntax(self):
        """Test handling of invalid YAML syntax"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write("invalid: yaml: syntax: [")  # Invalid YAML
            temp_path = f.name

        try:
            with pytest.raises(yaml.YAMLError):
                load_yaml_config(temp_path)
        finally:
            os.unlink(temp_path)

    def test_nonexistent_config_file(self):
        """Test handling of nonexistent config file"""
        import tempfile

        nonexistent_path = f"{tempfile.gettempdir()}/nonexistent_config.yaml"

        with pytest.raises(FileNotFoundError):
            load_yaml_config(nonexistent_path)

    def test_config_with_extra_fields(self):
        """Test that config ignores extra unknown fields"""
        config_data = {
            "admin": {"domain": "test.com", "email": "admin@test.com"},
            "unknown_field": "should_be_ignored",
        }

        # Should not raise an error due to extra field
        config = Config(**config_data)
        assert config.admin.domain == "test.com"

    def test_admin_context_user_defaults(self):
        """Test that AdminContext creates default users"""
        admin = AdminContext(domain="test.com", email="admin@test.com")

        # Should have default users
        assert len(admin.users) == 3
        usernames = [user.username for user in admin.users]
        assert "git" in usernames
        assert "admin" in usernames
        assert "test" in usernames

        # All users should have passwords
        for user in admin.users:
            assert user.password
            assert len(user.password) > 0
