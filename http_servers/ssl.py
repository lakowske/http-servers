from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from datetime import datetime, timedelta, timezone
from certbot import main as certbot_main
import requests
import logging
from .config import load_config, webroot_path, ssl_config_path
import os
import time

def healthcheck():
    url = 'http://localhost'
    try:
        response = requests.get(url)
        if response.status_code == 200:
            return True
    except requests.exceptions.ConnectionError:
        pass
    return False

def wait_for_webserver():
    """Wait for the web server to be ready"""
    max_attempts = 30
    attempt = 0

    while attempt < max_attempts:
        if healthcheck():
            return True
        time.sleep(1)
        attempt += 1

    return False

def setup_ssl(domains, email, staging=True):
    """
    Set up SSL certificates using certbot
    """
    config = load_config()

    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

    webroot = webroot_path(config)

    try:
        # Wait for web server to be ready
        if not wait_for_webserver():
            logger.error("Web server did not start in time")
            return False

        args = [
            '--authenticator', 'webroot',
            '--webroot-path', webroot,
            '--installer', 'None',
            '--email', email,
            '--agree-tos',
            '--no-eff-email',
            '-d', ','.join(domains),
            '--non-interactive',
            '--keep-until-expiring',
            '--expand'
        ]

        if staging:
            args.append('--staging')

        logger.info(f"Obtaining certificate for domains: {domains}")
        certbot_main.main(args)

        # Update Apache configuration
        ssl_config = ssl_config_path(config)
        with open(ssl_config, 'r') as f:
            config = f.read()

        # Replace certificate paths
        config = config.replace(
            'SSLCertificateFile "/usr/local/apache2/conf/server.crt"',
            f'SSLCertificateFile "/etc/letsencrypt/live/{domains[0]}/fullchain.pem"'
        )
        config = config.replace(
            'SSLCertificateKeyFile "/usr/local/apache2/conf/server.key"',
            f'SSLCertificateKeyFile "/etc/letsencrypt/live/{domains[0]}/privkey.pem"'
        )

        with open(ssl_config, 'w') as f:
            f.write(config)

        return True

    except Exception as e:
        logger.error(f"Failed to obtain certificate: {str(e)}")
        return False


def generate_self_signed_cert(domain, build_dir, country='US', state='Wisconsin', locality='Sun Prairie', organization='Acme Inc'):
    key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
    )

    subject = issuer = x509.Name([
        x509.NameAttribute(NameOID.COUNTRY_NAME, country),
        x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, state),
        x509.NameAttribute(NameOID.LOCALITY_NAME, locality),
        x509.NameAttribute(NameOID.ORGANIZATION_NAME, organization),
        x509.NameAttribute(NameOID.COMMON_NAME, domain),
    ])

    cert = x509.CertificateBuilder().subject_name(
        subject
    ).issuer_name(
        issuer
    ).public_key(
        key.public_key()
    ).serial_number(
        x509.random_serial_number()
    ).not_valid_before(
        datetime.now(timezone.utc)
    ).not_valid_after(
        datetime.now(timezone.utc) + timedelta(days=365)
    ).add_extension(
        x509.SubjectAlternativeName([x509.DNSName(domain)]),
        critical=False,
    ).sign(key, hashes.SHA256())

    cert_path = os.path.join(build_dir, f"server-cert.pem")
    key_path = os.path.join(build_dir, f"server-key.pem")

    with open(cert_path, "wb") as f:
        f.write(cert.public_bytes(serialization.Encoding.PEM))

    with open(key_path, "wb") as f:
        f.write(key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption()
        ))

    return cert_path, key_path