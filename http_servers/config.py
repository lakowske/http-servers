# config.py
import os
import yaml

from http_servers.paths import relative_to_absolute_path
default_domain = 'localhost'
default_email = 'admin@' + default_domain

DEFAULT_CONFIG = {
    'domain': default_domain,
    'email': default_email,
    'build_dir': 'build',
    'apache_dir': 'build/apache',
    'certbot_dir': 'build/certbot',
    'webroot_path': 'build/webroot',
    'container_webroot_path': '/usr/local/apache2/htdocs',
    'ssl_config_path': '/usr/local/apache2/conf/extra/httpd-ssl.conf'
}

_config_cache = {}

def load_config(config_file=None, reload=False):
    global _config_cache
    if config_file is None:
        config_file = relative_to_absolute_path('config.yaml')
    elif not os.path.isabs(config_file):
        config_file = relative_to_absolute_path(config_file)

    # Verify that the config_file exists
    if not os.path.exists(config_file):
        raise FileNotFoundError(f"Config file not found: {config_file}")

    if config_file not in _config_cache or reload:
        config = DEFAULT_CONFIG.copy()
        if os.path.exists(config_file):
            with open(config_file, 'r') as file:
                user_config = yaml.safe_load(file)
                if user_config is not None:
                    config.update(user_config)
        _config_cache[config_file] = config
    return _config_cache[config_file]

def email(config):
    return config['email']

def domain(config):
    return config['domain']

def build_dir(config):
    return relative_to_absolute_path(config['build_dir'])

def apache_dir(config):
    return relative_to_absolute_path(config['apache_dir'])

def apache_ssl_dir(config):
    return relative_to_absolute_path(config['apache_dir'] + '/conf/ssl')

def certbot_dir(config):
    return relative_to_absolute_path(config['certbot_dir'])

def certbot_config_dir(config):
    return relative_to_absolute_path(config['certbot_dir'] + '/conf')

def certbot_work_dir(config):
    return relative_to_absolute_path(config['certbot_dir'] + '/work')

def certbot_logs_dir(config):
    return relative_to_absolute_path(config['certbot_dir'] + '/logs')

def webroot_path(config):
    return relative_to_absolute_path(config['webroot_path'])

def ssl_config_path(config):
    return relative_to_absolute_path(config['ssl_config_path'])