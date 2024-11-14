"""
This module provides functionality to authenticate users for an Apache HTTP server.
It can generate random passwords, store them in a file, and check if a given password is correct.
"""
from passlib.apache import HtpasswdFile
import os

def generate_htpasswd(username, password):
    """
    Generates a new htpasswd entry for the given username and password.

    Args:
        username (str): The username.
        password (str): The password.

    Returns:
        str: The htpasswd entry.
    """
    ht = HtpasswdFile()
    ht.set_password(username, password)
    return ht.to_string().decode("utf-8")