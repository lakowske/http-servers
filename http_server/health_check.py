"""
This module contains a function to perform a healthcheck on a domain by making
HTTP and HTTPS requests.
"""

import logging
import requests


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def healthcheck(domain):
    """
    Perform a healthcheck on a domain by making HTTP and HTTPS requests.
    """

    http_url = f"http://{domain}"
    https_url = f"https://{domain}"

    try:
        http_response = requests.get(http_url, timeout=5)
        if http_response.status_code != 200:
            return False
    except requests.exceptions.ConnectionError as e:
        logger.error("HTTP healthcheck failed for %s: %s", http_url, e)
        return False

    try:
        https_response = requests.get(https_url, verify=False, timeout=5)
        if https_response.status_code != 200:
            return False
    except requests.exceptions.ConnectionError as e:
        logger.error("HTTPS healthcheck failed for %s: %s", https_url, e)
        return False

    return True
