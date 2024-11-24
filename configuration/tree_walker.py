"""
Tree walking functions for dealing with configuration trees.
"""

from pydantic import BaseModel
from configuration.tree import FSTree, TemplateTree


class TreeWalker:
    """A class to walk through FSTree nodes"""

    def walk(self, node: FSTree, context: BaseModel):
        """Walk through the tree and print the paths"""
        if isinstance(node, TemplateTree):
            self.on_template_tree(node, context)
        else:
            self.on_fs_tree(node, context)

        for child in node.children:
            self.walk(child, context)

    def on_fs_tree(self, node: FSTree, context: BaseModel):
        """Handle an FSTree node"""
        print(f"FSTree: {node.name}")
        print(f"Path: {node.path}")
        print(f"IsDir: {node.isDir}")

    def on_template_tree(self, node: TemplateTree, context: BaseModel):
        """Handle a TemplateTree node"""
        print(f"TemplateTree: {node.template_path}")
        print(f"Name: {node.name}")
        print(f"Path: {node.path}")


class TreeRenderer:
    """A class to render FSTree nodes to the filesystem"""

    def walk(self, node: FSTree, context: BaseModel):
        """Walk through the tree and render the paths"""
        if isinstance(node, TemplateTree):
            self.on_template_tree(node, context)
        else:
            self.on_fs_tree(node, context)

        for child in node.children:
            self.walk(child, context)

    def on_fs_tree(self, node: FSTree, context: BaseModel):
        """Handle an FSTree node"""
        node.make_path(context.build_root)

    def on_template_tree(self, node: TemplateTree, context: BaseModel):
        """Handle a TemplateTree node"""
        node.render(context.build_root, context.template_root)


def print_tree(node: FSTree, context: BaseModel):
    """Print the tree"""
    walker = TreeWalker()
    walker.walk(node, BaseModel())


def render_tree(node: FSTree, context: BaseModel):
    """Render the tree to the filesystem"""
    walker = TreeRenderer()
    walker.walk(node, context)
