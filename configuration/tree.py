import os
from typing import List, Optional
from pydantic import BaseModel, Field
import copy
from jinja2 import Environment, FileSystemLoader


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

    def get(self, name: str) -> Optional["FSTree"]:
        """Get a child node by name"""
        for child in self.children:
            if child.name == name:
                return child
        return None

    def tree_root_path(self, build_root: str, apath: str = None) -> str:
        """Convert a path to a path relative to the tree and root"""
        if apath is None:
            apath = self.path
        if self.parent:
            abs_path = self.parent.tree_root_path(build_root) + f"/{apath}"
        else:
            abs_path = f"{build_root}/{apath}"
        return abs_path

    def make_path(self, build_root: str) -> str:
        """Create a directory or touch a file path"""

        abs_path = self.tree_root_path(build_root)
        # Touch a file if it is not a directory
        if not self.isDir:
            # Create the necessary directories
            os.makedirs(os.path.dirname(abs_path), exist_ok=True)
            with open(abs_path, "w"):
                return abs_path

        if not os.path.exists(abs_path):
            os.makedirs(abs_path)

        return abs_path

    def make_all_paths(self, build_root: str) -> List[str]:
        """Create all directory paths"""
        paths = []
        for child in self.children:
            if child.isDir:
                path = child.make_path(build_root)
                paths.append(path)
                sub_paths = child.make_all_paths(build_root)
                paths.extend(sub_paths)
            else:
                path = child.make_path(build_root)
                paths.append(path)
        return paths

    def clean(self, build_root: str):
        """Remove all created directories"""
        for child in self.children:
            if child.isDir:
                child.clean(build_root)
            else:
                abs_path = child.tree_root_path(build_root)
                if os.path.exists(abs_path):
                    os.remove(abs_path)
        abs_path = self.tree_root_path(build_root)
        if os.path.exists(abs_path):
            if not self.isDir:
                os.remove(abs_path)
            else:
                os.rmdir(abs_path)


class TemplateTree(FSTree):
    """A tree node made from a template"""

    template_path: str

    def __init__(self, **data):
        super().__init__(**data)
        self.isDir = False

    def render(self, build_root: str, template_root: Optional[str] = None, **kwargs):
        """Render a template to a file"""
        abs_path = self.make_path(build_root)
        template_root = template_root or build_root
        template_path = f"{template_root}/{self.template_path}"
        env = Environment(loader=FileSystemLoader(os.path.dirname(template_path)))
        template = env.get_template(os.path.basename(self.template_path))
        rendered_content = template.render(**kwargs)
        with open(abs_path, "w") as file:
            file.write(rendered_content)
        return abs_path


httpd_conf_template = TemplateTree(
    name="httpd.conf",
    template_path="httpd.conf.template",
)

httpd_ssl_template = TemplateTree(
    name="httpd-ssl.conf",
    template_path="httpd-ssl.conf.template",
)

git_conf_template = TemplateTree(
    name="httpd-git.conf",
    template_path="httpd-git.conf.template",
)

dockerfile_template = TemplateTree(
    name="Dockerfile",
    template_path="Dockerfile.httpd.template",
)

html_template = TemplateTree(
    name="index.html",
    template_path="index.html.template",
)

extra = FSTree(
    name="extra",
    children=[
        httpd_ssl_template,
        git_conf_template,
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
        httpd_conf_template,
    ],
)

apache = FSTree(
    name="apache",
    children=[
        apache_conf,
        FSTree(name="cgi-bin"),
        FSTree(name="git"),
        dockerfile_template,
    ],
)

webroot = FSTree(
    name="webroot",
    children=[
        html_template,
    ],
)

build = FSTree(
    name="build",
    children=[
        apache,
        webroot,
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
