"""
Test the tree walker
"""

from configuration.tree_walker import TreeWalker, TreeRenderer, TreeRemoval
from configuration.tree_nodes import build_tree
from configuration.app import Config, AdminContext

TREE_SIZE = 42


def test_print_walker():
    """
    Tests the TreeWalker.walk method by traversing a tree built with build_tree
    and a given Config. Asserts that the number of results returned matches the
    expected TREE_SIZE.
    """
    walker = TreeWalker()
    results = walker.walk(
        build_tree,
        Config(
            admin=AdminContext(domain="example.com", email="admin@example.com")
        ),
    )
    assert len(results) == TREE_SIZE


def test_tree_renderer():
    """
    Tests the TreeRenderer's ability to walk a build tree and render
    configuration files.

    This test: - Instantiates a TreeRenderer and a Config with an AdminContext.
    - Walks the build tree using the renderer and configuration. - Asserts that
    the number of results matches the expected tree size. - Verifies that a
    specific configuration file ('httpd-git.conf') is created. - Checks that
    the generated file contains the correct ServerAdmin directive.

    Raises:
        AssertionError: If the number of results is incorrect or the expected
        content is not found in the file.
    """
    walker = TreeRenderer()
    config = Config(
        admin=AdminContext(domain="example.com", email="admin@example.com")
    )
    results = walker.walk(build_tree, config)
    assert len(results) == TREE_SIZE
    # Verify that the files were created
    httpd_git = (
        build_tree.get("apache").get("conf").get("extra").get("httpd-git.conf")
    )

    abs_path = httpd_git.tree_root_path(config.build.build_root)
    with open(abs_path) as file:
        content = file.read()
        assert "ServerAdmin admin@example.com" in content


def test_tree_removal():
    """
    Tests the TreeRemoval class by performing a depth-first traversal on a tree
    structure using the provided configuration. Asserts that the number of
    results matches the expected TREE_SIZE, verifying correct tree traversal
    and removal behavior.
    """
    walker = TreeRemoval()
    config = Config(
        admin=AdminContext(domain="example.com", email="admin@example.com")
    )
    results = walker.depth_first(build_tree, config)
    assert len(results) == TREE_SIZE
