import os
from typing import List, Optional
from pydantic import BaseModel, Field
import copy


class FSTree(BaseModel):
    """A tree of build artifacts"""

    name: str
    path: Optional[str] = None
    isDir: bool = True
    parent: Optional["FSTree"] = Field(default=None, exclude=True)
    children: List["FSTree"] = []

    def __init__(self, **data):
        super().__init__(**data)
        for child in self.children:
            child.parent = self
        if self.path is None:
            self.path = self.name

    def __init__(self, **data):
        super().__init__(**data)
        for child in self.children:
            child.parent = self
        if self.path is None:
            self.path = self.name

    def get(self, name: str) -> Optional["FSTree"]:
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


extra = FSTree(
    name="extra",
    children=[
        FSTree(name="httpd-ssl.conf", isDir=False),
    ],
)

apache_conf = FSTree(
    name="conf",
    children=[
        extra,
        FSTree(name="live"),
        FSTree(name="ssl"),
        FSTree(name="letsencrypt"),
        FSTree(name="htpasswd", isDir=False),
        FSTree(name="passwd", isDir=False),
    ],
)

apache = FSTree(
    name="apache",
    children=[
        apache_conf,
        FSTree(name="cgi-bin"),
        FSTree(name="git"),
    ],
)

build = FSTree(
    name="build",
    children=[
        apache,
        FSTree(name="webroot"),
        FSTree(name="secrets"),
        FSTree(name="letsencrypt"),
    ],
)


container_paths = FSTree(
    name="container_apache",
    path="/usr/local/apache2",
    children=[
        FSTree(name="htdocs"),
        copy.deepcopy(apache_conf),
        FSTree(name="cgi-bin"),
        FSTree(name="git"),
    ],
)
