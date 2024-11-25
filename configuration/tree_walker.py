"""
Tree walking functions for dealing with configuration trees.
"""

from pydantic import BaseModel
from configuration.tree import FSTree, TemplateTree


class TreeWalker:
    """A class to walk through FSTree nodes"""

    def walk(self, node: FSTree, context: BaseModel):
        """Walk through the tree and process the nodes"""
        results = []

        result = None
        if isinstance(node, TemplateTree):
            result = self.on_template_tree(node, context)
        else:
            result = self.on_fs_tree(node, context)

        if result:
            results.append(result)

        for child in node.children:
            results.extend(self.walk(child, context))

        return results

    def depth_first(self, node: FSTree, context: BaseModel):
        """Walk through the tree and process the nodes"""
        results = []

        for child in node.children:
            results.extend(self.depth_first(child, context))

        result = None
        if isinstance(node, TemplateTree):
            result = self.on_template_tree(node, context)
        else:
            result = self.on_fs_tree(node, context)

        if result:
            results.append(result)

        return results

    def on_fs_tree(self, node: FSTree, context: BaseModel):
        """Handle an FSTree node"""
        print(f"FSTree: {node.name}")
        print(f"Path: {node.path}")
        print(f"IsDir: {node.isDir}")
        return node

    def on_template_tree(self, node: TemplateTree, context: BaseModel):
        """Handle a TemplateTree node"""
        print(f"TemplateTree: {node.template_path}")
        print(f"Name: {node.name}")
        print(f"Path: {node.path}")
        return node


class TreeRenderer(TreeWalker):
    """A class to render FSTree nodes to the filesystem"""

    def on_fs_tree(self, node: FSTree, context: BaseModel):
        """Handle an FSTree node"""
        return node.make_path(context.build_context.build_root)

    def on_template_tree(self, node: TemplateTree, context: BaseModel):
        """Handle a TemplateTree node"""
        return node.render(
            **context.to_kwargs(),
        )


class TreeRemoval(TreeWalker):
    """A class to remove FSTree nodes from the filesystem"""

    def on_fs_tree(self, node: FSTree, context: BaseModel):
        """Handle an FSTree node"""
        return node.rm_path(context.build_context.build_root)

    def on_template_tree(self, node: TemplateTree, context: BaseModel):
        """Handle a TemplateTree node"""
        return node.rm_path(context.build_context.build_root)


def print_tree(node: FSTree, context: BaseModel):
    """Print the tree"""
    walker = TreeWalker()
    walker.walk(node, BaseModel())


def render_tree(node: FSTree, context: BaseModel):
    """Render the tree to the filesystem"""
    walker = TreeRenderer()
    walker.walk(node, context)


def remove_tree(node: FSTree, context: BaseModel):
    """Remove the tree from the filesystem"""
    walker = TreeRemoval()
    walker.walk(node, context)
