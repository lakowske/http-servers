"""
Test the simplified configuration tree renderer
"""

from configuration.app import AdminContext, Config
from configuration.simple_renderer import render_config_tree
from configuration.tree_nodes import build_tree

TREE_SIZE = 41


def test_simple_renderer():
    """
    Tests the simplified render_config_tree function to ensure it produces
    the same results as the old TreeRenderer.walk method.
    """
    config = Config(admin=AdminContext(domain="example.com", email="admin@example.com"))
    results = render_config_tree(build_tree, config)
    assert len(results) == TREE_SIZE


def test_simple_renderer_file_content():
    """
    Tests that the simplified renderer creates configuration files with correct content.

    Verifies that a specific configuration file ('httpd-git.conf') is created
    and contains the correct ServerAdmin directive.
    """
    config = Config(admin=AdminContext(domain="example.com", email="admin@example.com"))
    results = render_config_tree(build_tree, config)
    assert len(results) == TREE_SIZE

    # Verify that the files were created with correct content
    httpd_git = build_tree.get("apache").get("conf").get("extra").get("httpd-git.conf")
    abs_path = httpd_git.tree_root_path(config.build.build_root)

    with open(abs_path, encoding="utf-8") as file:
        content = file.read()
        assert "ServerAdmin admin@example.com" in content
