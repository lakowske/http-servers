from configuration.tree_walker import TreeWalker, TreeRenderer
from configuration.tree import build
from configuration.app import Config


def test_print_walker():
    walker = TreeWalker()
    walker.walk(build, Config(domain="example.com", email="admin@example.com"))


def test_tree_renderer():
    walker = TreeRenderer()
    config = Config(domain="example.com", email="admin@example.com")
    walker.walk(build, config)
    # Verify that the files were created
    httpd_git = build.get("apache").get("conf").get("extra").get("httpd-git.conf")

    abs_path = httpd_git.tree_root_path(config.build_root)
    with open(abs_path) as file:
        content = file.read()


#        assert "ServerAdmin admin@example.com" in content
