import os
from configuration.tree import BuildPaths
from main import WORKSPACE


def test_build_tree():
    build_tree = BuildPaths()
    # Test default values
    assert build_tree.name == "build"
    # Test children
    assert len(build_tree.children) == 4
    apache = build_tree.get("apache")
    assert apache.name == "apache"
    assert len(apache.children) == 4
    apache_conf = build_tree.get("apache").get("conf")
    assert apache_conf.name == "conf"
    assert len(apache_conf.children) == 5
    # Test to_absolute_path
    abs_path = apache_conf.to_absolute_path(WORKSPACE)
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
    assert len(paths) == 13


def test_clean():
    build_tree = BuildPaths()
    build_tree.clean(WORKSPACE)

    paths = build_tree.make_all_paths(WORKSPACE)
    for path in paths:
        assert os.path.exists(path)

    build_tree.clean(WORKSPACE)
    for path in paths:
        assert not os.path.exists(path)


def test_schema_dump():
    build_tree = BuildPaths()
    schema = build_tree.model_json_schema()
    assert schema["name"] == "build"
