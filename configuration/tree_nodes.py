"""
This module contains the abstract nodes for the build process.
"""

import os
import copy
from typing import List, Optional
from jinja2 import Environment, FileSystemLoader
from auth.auth import UserCredential, to_htpasswd_file, to_passwd_file
from auth.certificates import generate_self_signed_cert
from pydantic import BaseModel, Field
from auth.auth import UserCredential
from auth.password import random_password


class AdminContext(BaseModel):
    """AdminContext is a configuration class for the admin user"""

    email: str
    domain: str
    country: str = "US"
    state: str = "Wisconsin"
    locality: str = "Sun Prairie"
    organization: str = "Acme Inc"
    users: List[UserCredential] = [
        UserCredential(username="git", password=random_password(20))
    ]


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
            parent_node: FSTree = self.parent
            abs_path = parent_node.tree_root_path(build_root) + f"/{apath}"
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
            # Check if the file exists, if not create it
            if not os.path.exists(abs_path):
                with open(abs_path, "w"):
                    return abs_path

        if not os.path.exists(abs_path):
            os.makedirs(abs_path)

        return abs_path

    def rm_path(self, build_root: str) -> str:
        """Remove a directory or file path"""
        abs_path = self.tree_root_path(build_root)
        if os.path.exists(abs_path):
            if self.isDir:
                os.rmdir(abs_path)
            else:
                os.remove(abs_path)
        return abs_path


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


class Htpasswd(FSTree):
    """A tree node that represents an htpasswd file"""

    def __init__(self, **data):
        super().__init__(**data)
        self.isDir = False

    def render(self, build_root: str, users: List[UserCredential]):
        """Render a template to a file"""
        abs_path = self.make_path(build_root)
        to_htpasswd_file(users, abs_path)
        return abs_path


class Passwd(FSTree):
    """A tree node that represents an passwd file"""

    def __init__(self, **data):
        super().__init__(**data)
        self.isDir = False

    def render(self, build_root: str, users: List[UserCredential]):
        """Render a template to a file"""
        abs_path = self.make_path(build_root)
        to_passwd_file(users, abs_path)
        return abs_path


class SelfSignedCerts(FSTree):
    """A tree node that represents a self-signed certificate"""

    def __init__(
        self,
        children=[FSTree(name="server-cert.pem"), FSTree(name="server-key.pem")],
        **data,
    ):
        super().__init__(children=children, **data)

    def render(self, build_root: str, admin_context: AdminContext):
        """Render a template to a file"""
        abs_path = self.make_path(build_root)
        generate_self_signed_cert(
            admin_context.domain,
            abs_path,
            country=admin_context.country,
            state=admin_context.state,
            locality=admin_context.locality,
            organization=admin_context.organization,
        )
        return abs_path


htpasswd = Htpasswd(name="htpasswd")
passwd = Passwd(name="passwd")
ssl = SelfSignedCerts(
    name="ssl",
    children=[
        FSTree(name="server-cert.pem", isDir=False),
        FSTree(name="server-key.pem", isDir=False),
    ],
)

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
        ssl,
        FSTree(name="live"),
        FSTree(name="letsencrypt"),
        FSTree(name="htpasswd", isDir=False),
        FSTree(name="passwd", isDir=False),
        httpd_conf_template,
        htpasswd,
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

secrets = FSTree(
    name="secrets",
    children=[
        passwd,
    ],
)

build = FSTree(
    name="build",
    children=[
        apache,
        webroot,
        secrets,
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
