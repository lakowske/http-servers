"""
Simplified configuration tree rendering without visitor pattern complexity.
"""

from typing import Any, List

from configuration.app import Config
from configuration.tree_nodes import (
    Copy,
    DovecotEmailMap,
    DovecotPasswd,
    FSTree,
    Htpasswd,
    Passwd,
    SelfSignedCerts,
    TemplateTree,
)


def render_config_tree(node: FSTree, context: Config) -> List[Any]:
    """
    Render configuration tree to filesystem using direct type checking.

    Replaces the complex visitor pattern with simple isinstance checks.
    Maintains identical functionality to TreeRenderer.walk().

    Args:
        node: The FSTree node to render
        context: The configuration context

    Returns:
        List of render results
    """
    results = []

    # Process current node based on its type
    result = None

    if isinstance(node, TemplateTree):
        kwargs = context.to_kwargs()
        result = node.render(**kwargs)
    elif isinstance(node, Copy):
        result = node.render(context.build.build_root)
    elif isinstance(node, (Htpasswd, Passwd)):
        result = node.render(context.build.build_root, users=context.admin.users)
    elif isinstance(node, DovecotEmailMap):
        result = node.render(context.build.build_root, admin_context=context.admin)
    elif isinstance(node, DovecotPasswd):
        result = node.render(context.build.build_root, admin_context=context.admin)
    elif isinstance(node, SelfSignedCerts):
        result = node.render(context.build.build_root, admin=context.admin)
    elif isinstance(node, FSTree):
        # Base FSTree case - just create the directory
        result = node.make_path(context.build.build_root)

    if result:
        results.append(result)

    # Process children recursively
    for child in node.children:
        results.extend(render_config_tree(child, context))

    return results
