"""
This module provides functionality to authenticate users for an Apache HTTP server.
It can generate random passwords, store them in a file, and check if a given password is correct.
"""

import os
from pathlib import Path
from dataclasses import dataclass
from typing import List
from passlib.apache import HtpasswdFile


@dataclass
class UserCredential:
    """
    Represents a user's credentials.
    """

    username: str
    password: str


def ensure_file_path(file_path: str) -> None:
    """Creates parent directories for file path if they don't exist"""
    path = Path(file_path)
    os.makedirs(path.parent, exist_ok=True)


def to_htpasswd_file(users: List[UserCredential], file_path):
    """
    Generates a new htpasswd file with the given users and passwords.

    Args:
        users (list): A list of tuples containing the username and password.
        file_path (str): The file path to write to.
    """
    # Test if file exists
    ensure_file_path(file_path)
    ht = HtpasswdFile(file_path, new=not os.path.exists(file_path))
    for user in users:
        ht.set_password(user.username, user.password)
    ht.save()


def from_htpasswd_file(file_path):
    """
    Reads the htpasswd file content from a file.

    Args:
        file_path (str): The file path to read from.

    Returns:
        str: The htpasswd file content.
    """
    ht = HtpasswdFile(file_path)
    return ht


def from_htpasswd_str(htpasswd_str):
    """
    Creates a HtpasswdFile object from a string.

    Args:
        htpasswd_str (str): The htpasswd file content.

    Returns:
        HtpasswdFile: The HtpasswdFile object.
    """
    ht = HtpasswdFile()
    ht.load_string(htpasswd_str)
    return ht


def to_htpasswd_str(user: UserCredential) -> str:
    """
    Generates a new htpasswd entry for the given username and password.

    Args:
        username (str): The username.
        password (str): The password.

    Returns:
        str: The htpasswd entry.
    """
    ht = HtpasswdFile()
    ht.set_password(user.username, user.password)
    return ht.to_string().decode("utf-8")


def to_passwd_file(users: List[UserCredential], file_path):
    """
    Generates a new plain text passwd file with the given users and passwords.

    Args:
        users (list): A list of tuples containing the username and password.
        file_path (str): The file path to write to.
    """
    # Test if file exists
    ensure_file_path(file_path)
    with open(file_path, "w") as f:
        for user in users:
            f.write(f"{user.username}:{user.password}\n")


def from_passwd_file(file_path):
    """
    Reads the passwd file content from a file.

    Args:
        file_path (str): The file path to read from.

    Returns:
        str: A list of UserCredential objects.
    """
    with open(file_path, "r") as f:
        users = []
        for line in f:
            username, password = line.strip().split(":")
            users.append(UserCredential(username, password))
        return users
