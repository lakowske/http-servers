import os
from typing import List, Optional
from pydantic import BaseModel


class BuildTree(BaseModel):
    """A tree of build directories"""

    name: str
    isDir: bool = True
    parent: Optional["BuildTree"] = None
    children: List["BuildTree"] = []

    def __init__(self, **data):
        super().__init__(**data)
        for child in self.children:
            child.parent = self

    def get(self, name: str) -> Optional["BuildTree"]:
        """Get a child node by name"""
        for child in self.children:
            if child.name == name:
                return child
        return None

    def to_absolute_path(self, root: str) -> str:
        """Convert a relative path to an absolute path"""
        if self.parent:
            abs_path = self.parent.to_absolute_path(root) + f"/{self.name}"
        else:
            abs_path = f"{root}/{self.name}"
        return abs_path

    def make_path(self, root: str) -> str:
        """Create a directory or touch a file path"""

        abs_path = self.to_absolute_path(root)
        # Touch a file if it is not a directory
        if not self.isDir:
            with open(abs_path, "w"):
                return abs_path

        if not os.path.exists(abs_path):
            os.makedirs(abs_path)

        return abs_path

    def make_all_paths(self, root: str) -> List[str]:
        """Create all directory paths"""
        paths = []
        for child in self.children:
            if child.isDir:
                path = child.make_path(root)
                paths.append(path)
                sub_paths = child.make_all_paths(root)
                paths.extend(sub_paths)
            else:
                path = child.make_path(root)
                paths.append(path)
        return paths

    def clean(self, root: str):
        """Remove all created directories"""
        for child in self.children:
            if child.isDir:
                child.clean(root)
            else:
                abs_path = child.to_absolute_path(root)
                if os.path.exists(abs_path):
                    os.remove(abs_path)
        abs_path = self.to_absolute_path(root)
        if os.path.exists(abs_path):
            if not self.isDir:
                os.remove(abs_path)
            else:
                os.rmdir(abs_path)


class ApacheConf(BuildTree):
    """Apache configuration paths"""

    name: str = "conf"
    children: List[BuildTree] = [
        BuildTree(name="extra"),
        BuildTree(name="live"),
        BuildTree(name="ssl"),
        BuildTree(name="htpasswd", isDir=False),
        BuildTree(name="passwd", isDir=False),
    ]


class Apache(BuildTree):
    """Apache configuration paths"""

    name: str = "apache"
    children: List[BuildTree] = [
        ApacheConf(),
        BuildTree(name="conf"),
        BuildTree(name="cgi-bin"),
        BuildTree(name="git"),
    ]


class BuildPaths(BuildTree):
    """Some configuration in a build directory"""

    name: str = "build"
    children: List[BuildTree] = [
        Apache(),
        BuildTree(name="webroot"),
        BuildTree(name="secrets"),
        BuildTree(name="letsencrypt"),
    ]
