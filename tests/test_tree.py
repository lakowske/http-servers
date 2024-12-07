import os
from configuration.tree_nodes import (
    build_tree,
    container_paths,
)
from configuration.app import WORKSPACE


def test_build_tree():
    # Test default values
    assert build_tree.name == "build"
    # Test children
    assert len(build_tree.children) == 5
    apache = build_tree.get("apache")
    assert apache.name == "apache"
    assert len(apache.children) == 5
    apache_conf = build_tree.get("apache").get("conf")
    assert apache_conf.name == "conf"
    assert len(apache_conf.children) == 8
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


def test_container_tree():
    container_tree = container_paths
    # Test default values
    assert container_tree.name == "container_apache"
    # Test children
    assert len(container_tree.children) == 4
    # Test to_absolute_path
    abs_path = container_tree.tree_root_path(WORKSPACE)
    assert abs_path == f"{WORKSPACE}/{container_tree.path}"


def test_schema_dump():

    schema = build_tree.model_json_schema()
    assert schema["$defs"]["FSTree"]["description"] == "A tree of build artifacts"
    assert "build" == build_tree.name
