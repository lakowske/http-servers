"""
Test the tree walker
"""

from configuration.tree_walker import TreeWalker, TreeRenderer, TreeRemoval
from configuration.tree_nodes import build_tree
from configuration.app import Config, AdminContext

TREE_SIZE = 29


def test_print_walker():
    walker = TreeWalker()
    results = walker.walk(
        build_tree,
        Config(admin=AdminContext(domain="example.com", email="admin@example.com")),
    )
    assert len(results) == TREE_SIZE


def test_tree_renderer():
    walker = TreeRenderer()
    config = Config(admin=AdminContext(domain="example.com", email="admin@example.com"))
    results = walker.walk(build_tree, config)
    assert len(results) == TREE_SIZE
    # Verify that the files were created
    httpd_git = build_tree.get("apache").get("conf").get("extra").get("httpd-git.conf")

    abs_path = httpd_git.tree_root_path(config.build.build_root)
    with open(abs_path) as file:
        content = file.read()
        assert "ServerAdmin admin@example.com" in content


def test_tree_removal():
    walker = TreeRemoval()
    config = Config(admin=AdminContext(domain="example.com", email="admin@example.com"))
    results = walker.depth_first(build_tree, config)
    assert len(results) == TREE_SIZE
