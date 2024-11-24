import os
from configuration.tree import (
    build,
    container_paths,
    httpd_conf_template,
    httpd_ssl_template,
)
from configuration.app import WORKSPACE


def test_build_tree():
    build_tree = build
    # Test default values
    assert build_tree.name == "build"
    # Test children
    assert len(build_tree.children) == 4
    apache = build_tree.get("apache")
    assert apache.name == "apache"
    assert len(apache.children) == 4
    apache_conf = build_tree.get("apache").get("conf")
    assert apache_conf.name == "conf"
    assert len(apache_conf.children) == 7
    # Test to_absolute_path
    abs_path = apache_conf.tree_root_path(WORKSPACE)
    assert abs_path == f"{WORKSPACE}/build/apache/conf"
    # Test make_path
    abs_path = apache_conf.make_path(WORKSPACE)
    assert abs_path == f"{WORKSPACE}/build/apache/conf"
    apache_conf_ssl = apache_conf.get("ssl")
    assert apache_conf_ssl.name == "ssl"
    apache_conf_ssl_path = apache_conf_ssl.make_path(WORKSPACE)
    # Verify path creation
    assert os.path.exists(abs_path)
    assert os.path.exists(apache_conf_ssl_path)
    # Test make_all_paths
    paths = build_tree.make_all_paths(WORKSPACE)
    assert len(paths) == 18


def test_container_tree():
    container_tree = container_paths
    # Test default values
    assert container_tree.name == "container_apache"
    # Test children
    assert len(container_tree.children) == 4
    # Test to_absolute_path
    abs_path = container_tree.tree_root_path(WORKSPACE)
    assert abs_path == f"{WORKSPACE}/{container_tree.path}"


def test_clean():
    build_tree = build
    build_tree.clean(WORKSPACE)

    paths = build_tree.make_all_paths(WORKSPACE)
    for path in paths:
        assert os.path.exists(path)

    build_tree.clean(WORKSPACE)
    for path in paths:
        assert not os.path.exists(path)


def test_schema_dump():

    schema = build.model_json_schema()
    assert schema["$defs"]["FSTree"]["description"] == "A tree of build artifacts"
    assert "build" == build.name


def test_tree_template():
    """Test the tree template"""
    abs_path = httpd_conf_template.render(
        WORKSPACE, domain="example.com", email="admin@example.com"
    )
    assert os.path.exists(abs_path)
    with open(abs_path, "r") as file:
        content = file.read()
        assert "example.com" in content
        assert "admin@example.com" in content
