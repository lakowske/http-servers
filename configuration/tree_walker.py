"""
Tree walking functions for dealing with configuration trees.
"""

from configuration.app import Config
from configuration.tree_nodes import (
    FSTree,
    TemplateTree,
    Htpasswd,
    Passwd,
    SelfSignedCerts,
)


class TreeWalker:
    """A class to walk through FSTree nodes.  Users may optionally override
    the type specific methods to handle different types of nodes, and/or specify
    a default method to handle nodes that aren't specifically defined."""

    def walk(self, node: FSTree, context: Config):
        """Walk through the tree and process the nodes"""
        results = []

        result = self.process_node(node, context)
        if result:
            results.append(result)

        for child in node.children:
            results.extend(self.walk(child, context))

        return results

    def depth_first(self, node: FSTree, context: Config):
        """Walk through the tree and process the nodes"""
        results = []

        for child in node.children:
            results.extend(self.depth_first(child, context))

        result = self.process_node(node, context)
        if result:
            results.append(result)

        return results

    def process_node(self, node: FSTree, context: Config):
        """Process a node based on its type"""
        if isinstance(node, TemplateTree):
            return self.call_method("on_template_tree", node, context)
        elif isinstance(node, Htpasswd):
            return self.call_method("on_htpasswd", node, context)
        elif isinstance(node, Passwd):
            return self.call_method("on_passwd", node, context)
        elif isinstance(node, SelfSignedCerts):
            return self.call_method("on_self_signed_certs", node, context)
        elif isinstance(node, FSTree):
            return self.call_method("on_fs_tree", node, context)
        else:
            raise ValueError(f"Unknown node type: {node}")

    def call_method(self, method_name: str, node: FSTree, context: Config):
        """Call a method if it exists, otherwise call a default method"""
        default_method = getattr(self, "default", self.default)
        method = getattr(self, method_name, default_method)
        return method(node, context)

    def default(self, node: FSTree, context: Config):
        """Handle an FSTree node"""
        return node


class TreeSimplePrinter(TreeWalker):

    def default(self, node: FSTree, context: Config):
        """Handle an FSTree node"""
        print(f"FSTree: {node.name}")
        print(f"Path: {node.path}")
        print(f"IsDir: {node.isDir}")
        return node


class TreePrinter(TreeWalker):

    def on_fs_tree(self, node: FSTree, context: Config):
        """Handle an FSTree node"""
        print(f"FSTree: {node.name}")
        print(f"Path: {node.path}")
        print(f"IsDir: {node.isDir}")
        return node

    def on_template_tree(self, node: TemplateTree, context: Config):
        """Handle a TemplateTree node"""
        print(f"TemplateTree: {node.template_path}")
        print(f"Name: {node.name}")
        print(f"Path: {node.path}")
        return node

    def on_htpasswd(self, node: Htpasswd, context: Config):
        """Handle an Htpasswd node"""
        print(f"Htpasswd: {node.name}")
        print(f"Path: {node.path}")
        return node

    def on_passwd(self, node: Passwd, context: Config):
        """Handle an Passwd node"""
        print(f"Passwd: {node.name}")
        print(f"Path: {node.path}")
        return node

    def on_self_signed_certs(self, node: SelfSignedCerts, context: Config):
        """Handle an SelfSignedCerts node"""
        print(f"SelfSignedCerts: {node.name}")
        print(f"Path: {node.path}")
        return node


class TreeRenderer(TreeWalker):
    """A class to render FSTree nodes to the filesystem"""

    def on_fs_tree(self, node: FSTree, context: Config):
        """Handle an FSTree node"""
        return node.make_path(context.build.build_root)

    def on_template_tree(self, node: TemplateTree, context: Config):
        """Handle a TemplateTree node"""
        return node.render(
            **context.to_kwargs(),
        )

    def on_htpasswd(self, node: Htpasswd, context: Config):
        return node.render(context.build.build_root, users=context.admin.users)

    on_passwd = on_htpasswd

    def on_self_signed_certs(self, node: SelfSignedCerts, context: Config):
        return node.render(context.build.build_root, admin=context.admin)


class TreeRemoval(TreeWalker):
    """A class to remove FSTree nodes from the filesystem"""

    def default(self, node: FSTree, context: Config):
        """Handle an FSTree node"""
        return node.rm_path(context.build.build_root)


def print_tree(node: FSTree, context: Config):
    """Print the tree"""
    walker = TreeWalker()
    walker.walk(node, Config())


def render_tree(node: FSTree, context: Config):
    """Render the tree to the filesystem"""
    walker = TreeRenderer()
    walker.walk(node, context)


def remove_tree(node: FSTree, context: Config):
    """Remove the tree from the filesystem"""
    walker = TreeRemoval()
    walker.walk(node, context)
