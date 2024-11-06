# config.py
import os
import yaml

DEFAULT_CONFIG = {
    'build_dir': 'build',
    'apache_dir': 'apache',
    'certbot_dir': 'certbot',
    'webroot_path': '/usr/local/apache2/htdocs',
    'ssl_config_path': '/usr/local/apache2/conf/extra/httpd-ssl.conf'
}

_config_cache = None

def load_config(reload=False):
    global _config_cache
    if _config_cache is None or reload:
        config = DEFAULT_CONFIG.copy()
        config_path = os.path.join(os.path.dirname(__file__), '..', 'config.yaml')
        if os.path.exists(config_path):
            with open(config_path, 'r') as file:
                user_config = yaml.safe_load(file)
                config.update(user_config)
        _config_cache = config
    return _config_cache

def build_dir(config):
    return os.path.join(os.path.dirname(__file__), '..', config['build_dir'])

def apache_dir(config):
    return os.path.join(build_dir(config), config['apache_dir'])

def certbot_dir(config):
    return os.path.join(build_dir(config), config['certbot_dir'])

def webroot_path(config):
    return config['webroot_path']

def ssl_config_path(config):
    return config['ssl_config_path']