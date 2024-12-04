from configuration.tree_walker import TreeWalker, TreeRenderer, TreeRemoval
from configuration.tree_nodes import build
from configuration.app import Config, AdminContext

tree_size = 27


def test_print_walker():
    walker = TreeWalker()
    results = walker.walk(
        build,
        Config(
            admin_context=AdminContext(domain="example.com", email="admin@example.com")
        ),
    )
    assert len(results) == tree_size


def test_tree_renderer():
    walker = TreeRenderer()
    config = Config(
        admin_context=AdminContext(domain="example.com", email="admin@example.com")
    )
    results = walker.walk(build, config)
    assert len(results) == tree_size
    # Verify that the files were created
    httpd_git = build.get("apache").get("conf").get("extra").get("httpd-git.conf")

    abs_path = httpd_git.tree_root_path(config.build_context.build_root)
    with open(abs_path) as file:
        content = file.read()
        assert "ServerAdmin admin@example.com" in content


def test_tree_removal():
    walker = TreeRemoval()
    config = Config(
        admin_context=AdminContext(domain="example.com", email="admin@example.com")
    )
    results = walker.depth_first(build, config)
    assert len(results) == tree_size
