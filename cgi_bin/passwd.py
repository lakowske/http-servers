#!/usr/bin/env python3

import os
import html
from passlib.apache import HtpasswdFile

PAGE_TEMPLATE = """
Content-Type: text/html

<html>
<head>
    <title>CGI Script</title>
</head>
<body>
    Hello world!
</body>
</html>
"""


def generate_directory_listing():
    items = os.listdir(".")
    return generate_html_list("Directory Listing", items)


def generate_environment_variables():
    items = [f"{key}: {value}" for key, value in os.environ.items()]
    return generate_html_list("Environment Variables", items)


def generate_html_list(title, items):
    output = []
    output.append(f"<h1>{html.escape(title)}</h1>")
    output.append("<ul>")
    for item in items:
        output.append(f"<li>{html.escape(item)}</li>")
    output.append("</ul>")
    return "\n".join(output)


def generate_htpasswd(username, password):
    ht = HtpasswdFile()
    ht.set_password(username, password)
    return ht.to_string().decode("utf-8")


def generate_page(content):
    return PAGE_TEMPLATE.format(content=content)


if __name__ == "__main__":
    content = []
    content.append(generate_directory_listing())
    content.append(generate_environment_variables())

    # Example usage of generate_htpasswd
    # htpasswd_entry = generate_htpasswd("user", "password")
    # content.append(f"<pre>{html.escape(htpasswd_entry)}</pre>")

    full_content = "\n".join(content)
    print(generate_page(full_content))
