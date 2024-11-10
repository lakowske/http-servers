import os
import click
from .config import load_config, build_dir, apache_ssl_dir, webroot_path
from .ssl import generate_self_signed_cert

def read_template(file_path):
    base_dir = os.path.dirname(__file__)
    full_path = os.path.join(base_dir, '..', 'templates', file_path)
    with open(full_path, 'r') as file:
        return file.read()

def write_file(file_path, content):
    with open(file_path, 'w') as file:
        file.write(content)

def build_templates(domain, email, config=None):
    if config is None:
        config = load_config()
    template_build_dir = build_dir(config)

    ssl_dir = os.path.join(template_build_dir, 'apache/conf/ssl')
    os.makedirs(ssl_dir, exist_ok=True)
    os.makedirs(os.path.join(template_build_dir, 'apache/conf/live'), exist_ok=True)
    os.makedirs(os.path.join(template_build_dir, 'apache/conf/extra'), exist_ok=True)
    os.makedirs(os.path.join(template_build_dir, 'webroot'), exist_ok=True)
    os.makedirs(os.path.join(template_build_dir, 'letsencrypt'), exist_ok=True)
    os.makedirs(os.path.join(template_build_dir, 'certbot'), exist_ok=True)
    os.makedirs(os.path.join(template_build_dir, 'certbot/conf'), exist_ok=True)
    os.makedirs(os.path.join(template_build_dir, 'certbot/work'), exist_ok=True)
    os.makedirs(os.path.join(template_build_dir, 'certbot/logs'), exist_ok=True)
    # Generate self-signed certificate for development and initialisation
    generate_self_signed_cert(domain, ssl_dir)

    httpd_conf_template = read_template('httpd.conf.template')
    httpd_conf_content = httpd_conf_template.replace('{{ domain }}', domain).replace('{{ email }}', email)
    write_file(os.path.join(template_build_dir, 'apache/conf/httpd.conf'), httpd_conf_content)

    ssl_conf_template = read_template('httpd-ssl.conf.template')
    ssl_conf_content = ssl_conf_template.replace('{{ domain }}', domain).replace('{{ email }}', email)
    write_file(os.path.join(template_build_dir, 'apache/conf/extra/httpd-ssl.conf'), ssl_conf_content)

    dockerfile_httpd_template = read_template('Dockerfile.httpd.template')
    dockerfile_httpd_content = dockerfile_httpd_template
    write_file(os.path.join(template_build_dir, 'apache/Dockerfile'), dockerfile_httpd_content)

    html_template = read_template('index.html.template')
    html_content = html_template.replace('{{ domain }}', domain).replace('{{ email }}', email)
    write_file(os.path.join(template_build_dir, 'webroot/index.html'), html_content)





@click.command()
@click.option('--domain', required=True, help='The domain name for the SSL certificate.')
@click.option('--email', required=True, help='The email address for the SSL certificate registration.')
def templates(domain):
    build_templates(domain)