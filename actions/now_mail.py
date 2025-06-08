#!/usr/local/venv/bin/python
"""
A python script to handle user mail operations, like creating a new user,
deleting a user, and listing all users.
"""

import os
from DynamicCLI import DynamicCLI

cli = DynamicCLI()


@cli.register()
def list_all_users(file_path="/etc/dovecot/passwd"):
    """
    Read all users from the dovecot mail password file.
    Returns:
        list: A list of usernames.
    """
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            users = file.readlines()
        return [user.strip() for user in users]
    except FileNotFoundError:
        return []


@cli.register()
def has_user(username, domain, file_path="/etc/dovecot/passwd"):
    """
    Check if a user exists in the dovecot mail password file.

    Args:
        username (str): The username to check.
        domain (str): The domain of the user.
        file_path (str): The path to the dovecot password file.

    Returns:
        bool: True if the user exists, False otherwise.
    """
    existing_users = list_all_users(file_path)
    return f"{username}@{domain}" in existing_users


@cli.register()
def create_dovecot_user(username, password, domain, file_path="/etc/dovecot/passwd"):
    """
    Create a new user in the dovecot mail password file.

    Args:
        username (str): The username of the new user.
        password (str): The password for the new user.
        domain (str): The domain for the new user.
        file_path (str): The path to the dovecot password file.

    Returns:
        bool: True if the user was created successfully, False otherwise.
    """
    # Check if the user already exists
    existing_users = list_all_users(file_path)
    if f"{username}@{domain}" in existing_users:
        print(f"User {username}@{domain} already exists.")
        return False

    try:
        with open(file_path, "a", encoding="utf-8") as file:
            file.write(f"{username}@{domain}:{{PLAIN}}{password}\n")
        return True
    except OSError as e:
        print(f"Error creating user: {e}")
        return False


@cli.register()
def delete_dovecot_user(username, domain, file_path="/etc/dovecot/passwd"):
    """
    Delete a user from the dovecot mail password file.

    Args:
        username (str): The username of the user to delete.
        domain (str): The domain of the user to delete.
        file_path (str): The path to the dovecot password file.

    Returns:
        bool: True if the user was deleted successfully, False otherwise.
    """
    existing_users = list_all_users(file_path)
    user_to_delete = f"{username}@{domain}"

    if user_to_delete not in existing_users:
        print(f"User {user_to_delete} does not exist.")
        return False

    try:
        with open(file_path, "w", encoding="utf-8") as file:
            for user in existing_users:
                if user != user_to_delete:
                    file.write(user + "\n")
        return True
    except OSError as e:
        print(f"Error deleting user: {e}")
        return False


@cli.register()
def list_all_mailboxes(mailbox_map_file="/etc/postfix/virtual_mailbox_maps"):
    """
    List all mailboxes from the Postfix virtual mailbox maps file.

    Args:
        mailbox_map_file (str): The path to the Postfix virtual mailbox maps
        file.

    Returns:
        list: A list of mailboxes.
    """
    try:
        with open(mailbox_map_file, "r", encoding="utf-8") as file:
            mailboxes = file.readlines()
        return [mailbox.strip() for mailbox in mailboxes if mailbox.strip()]
    except FileNotFoundError:
        return []


@cli.register()
def has_user_mailbox_map(username, domain, mailbox_map_file="/etc/postfix/virtual_mailbox_maps"):
    """
    Check if a mailbox map entry for the user exists in the Postfix virtual
    mailbox maps file.

    Args:
        username (str): The username of the user.
        domain (str): The domain of the user.
        mailbox_map_file (str): The path to the Postfix virtual mailbox maps
        file.

    Returns:
        bool: True if the mailbox map entry exists, False otherwise.
    """
    existing_mailboxes = list_all_mailboxes(mailbox_map_file)
    mailbox_entry = f"{username}@{domain} {domain}/{username}/"
    return mailbox_entry in existing_mailboxes


@cli.register()
def create_user_mailbox_map(username, domain, mailbox_map_file="/etc/postfix/virtual_mailbox_maps"):
    """
    Create a mailbox map entry for the user in the Postfix virtual mailbox maps
    file.

    Args:
        username (str): The username of the user. domain (str): The domain of
        the user. mailbox_map_file (str): The path to the Postfix virtual
        mailbox maps file.

    Returns:
        bool: True if the mailbox map entry was created successfully, False
        otherwise.
    """
    existing_mailboxes = list_all_mailboxes(mailbox_map_file)
    mailbox_entry = f"{username}@{domain} {domain}/{username}/\n"
    if mailbox_entry in existing_mailboxes:
        print(f"Mailbox entry for {username}@{domain} already exists.")
        return False
    try:
        with open(mailbox_map_file, "a", encoding="utf-8") as file:
            file.write(mailbox_entry)
        return True
    except OSError as e:
        print(f"Error creating mailbox map entry: {e}")
        return False


@cli.register()
def delete_user_mailbox_map(username, domain, mailbox_map_file="/etc/postfix/virtual_mailbox_maps"):
    """
    Delete a mailbox map entry for the user in the Postfix virtual mailbox maps
    file.

    Args:
        username (str): The username of the user.
        domain (str): The domain of the user.
        mailbox_map_file (str): The path to the Postfix virtual mailbox maps
        file.

    Returns:
        bool: True if the mailbox map entry was deleted successfully, False
        otherwise.
    """
    existing_mailboxes = list_all_mailboxes(mailbox_map_file)
    mailbox_entry = f"{username}@{domain} {domain}/{username}/\n"
    if mailbox_entry not in existing_mailboxes:
        print(f"Mailbox entry for {username}@{domain} does not exist.")
        return False

    try:
        with open(mailbox_map_file, "w", encoding="utf-8") as file:
            for mailbox in existing_mailboxes:
                if mailbox != mailbox_entry.strip():
                    file.write(mailbox + "\n")
        return True
    except OSError as e:
        print(f"Error deleting mailbox map entry: {e}")
        return False


@cli.register()
def create_user_mailbox(username, domain, mail_dir="/var/vmail"):
    """
    Create a mailbox directory for the user.

    Args:
        username (str): The username of the user.
        domain (str): The domain of the user.
        mail_dir (str): The base directory for mailboxes.

    Returns:
        bool: True if the mailbox was created successfully, False otherwise.
    """

    mailbox_path = os.path.join(mail_dir, f"{domain}/{username}")

    try:
        os.makedirs(mailbox_path, exist_ok=True)
        return True
    except OSError as e:
        print(f"Error creating mailbox: {e}")
        return False


@cli.register()
def has_user_mailbox(username, domain, mail_dir="/var/vmail"):
    """
    Check if a mailbox directory for the user exists.

    Args:
        username (str): The username of the user.
        domain (str): The domain of the user.
        mail_dir (str): The base directory for mailboxes.

    Returns:
        bool: True if the mailbox exists, False otherwise.
    """

    mailbox_path = os.path.join(mail_dir, f"{domain}/{username}")
    return os.path.exists(mailbox_path)


@cli.register()
def delete_user_mailbox(username, domain, mail_dir="/var/vmail"):
    """
    Delete a mailbox directory for the user.

    Args:
        username (str): The username of the user.
        domain (str): The domain of the user.
        mail_dir (str): The base directory for mailboxes.

    Returns:
        bool: True if the mailbox was deleted successfully, False otherwise.
    """
    mailbox_path = os.path.join(mail_dir, f"{domain}/{username}")

    try:
        if os.path.exists(mailbox_path):
            os.rmdir(mailbox_path)
            return True
        else:
            print(f"Mailbox {mailbox_path} does not exist.")
            return False
    except OSError as e:
        print(f"Error deleting mailbox: {e}")
        return False


@cli.register()
def list_all_domains(domain_file="/etc/postfix/virtual_mailbox_domains"):
    """
    List all domains from the Postfix virtual mailbox domains file.

    Args:
        domain_file (str): The path to the Postfix virtual mailbox domains
        file.

    Returns:
        list: A list of domains.
    """
    try:
        with open(domain_file, "r", encoding="utf-8") as file:
            domains = file.readlines()
        return [domain.strip().split()[0] for domain in domains if domain.strip()]
    except FileNotFoundError:
        return []


@cli.register()
def has_domain(domain, domain_file="/etc/postfix/virtual_mailbox_domains"):
    """
    Check if a domain exists in the Postfix virtual mailbox domains file.

    Args:
        domain (str): The domain to check.
        domain_file (str): The path to the Postfix virtual mailbox domains
        file.

    Returns:
        bool: True if the domain exists, False otherwise.
    """
    existing_domains = list_all_domains(domain_file)
    return domain in existing_domains


@cli.register()
def create_domain(domain, domain_file="/etc/postfix/virtual_mailbox_domains"):
    """
    Create a domain entry in the Postfix virtual mailbox domains file if it
    does not exist.

    Args:
        domain_file (str): The path to the Postfix virtual mailbox domains
        file.

    Returns:
        bool: True if the domain was created successfully, False otherwise.
    """
    existing_domains = list_all_domains(domain_file)
    if domain in existing_domains:
        print(f"Domain {domain} already exists.")
        return False

    try:
        with open(domain_file, "a", encoding="utf-8") as file:
            file.write(f"{domain} OK\n")
        return True
    except OSError as e:
        print(f"Error creating domain: {e}")
        return False


@cli.register()
def delete_domain(domain, domain_file="/etc/postfix/virtual_mailbox_domains"):
    """
    Delete a domain entry from the Postfix virtual mailbox domains file.

    Args:
        domain (str): The domain to delete. domain_file (str): The path to the
        Postfix virtual mailbox domains file.

    Returns:
        bool: True if the domain was deleted successfully, False otherwise.
    """
    existing_domains = list_all_domains(domain_file)
    if domain not in existing_domains:
        print(f"Domain {domain} does not exist.")
        return False

    try:
        with open(domain_file, "w", encoding="utf-8") as file:
            for d in existing_domains:
                if d != domain:
                    file.write(f"{d} OK\n")
        return True
    except OSError as e:
        print(f"Error deleting domain: {e}")
        return False


@cli.register()
def run_postmap(
    domain_file="/etc/postfix/virtual_mailbox_domains",
    mailbox_map_file="/etc/postfix/virtual_mailbox_maps",
    vmailbox_file="/etc/postfix/vmailbox",
):
    """
    Run postmap on the specified files to update Postfix maps.

    Args:
        domain_file (str): The path to the Postfix virtual mailbox domains
        file.
        mailbox_map_file (str): The path to the Postfix virtual mailbox
        maps file.
        vmailbox_file (str): The path to the Postfix vmailbox file.

    Returns:
        bool: True if postmap was run successfully, False otherwise.
    """
    try:
        # Copy the virtual mailbox maps to vmailbox file
        with open(vmailbox_file, "w", encoding="utf-8") as vfile:
            with open(mailbox_map_file, "r", encoding="utf-8") as mfile:
                for line in mfile:
                    if line.strip():
                        vfile.write(line)
        # Run postmap on the specified files
        os.system(f"postmap {domain_file}")
        os.system(f"postmap {mailbox_map_file}")
        os.system(f"postmap {vmailbox_file}")
        return True
    except OSError as e:
        print(f"Error running postmap: {e}")
        return False


@cli.register()
def create_user(
    username,
    password,
    domain,
    domain_file="/etc/postfix/virtual_mailbox_domains",
    mailbox_map_file="/etc/postfix/virtual_mailbox_maps",
    mail_dir="/var/vmail",
    dovecot_file="/etc/dovecot/passwd",
):
    """
    Create a new user with a mailbox and a domain.

    Args:
        username (str): The username of the new user.
        password (str): The password for the new user.
        domain (str): The domain for the new user.
        mail_dir (str): The base directory for mailboxes.
        dovecot_file (str): The path to the dovecot password file.

    Returns:
        bool: True if the user was created successfully, False otherwise.
    """
    if not has_domain(domain, domain_file):
        if not create_domain(domain, domain_file):
            return False
    if not has_user(username, domain, dovecot_file):
        if not create_dovecot_user(username, password, domain, dovecot_file):
            return False
    if has_user_mailbox_map(username, domain, mailbox_map_file):
        print(f"Mailbox map entry for {username}@{domain} already exists.")
        return False
    else:
        print(f"Creating mailbox map entry for {username}@{domain}.")
        if not create_user_mailbox_map(username, domain, mailbox_map_file):
            return False

    if not has_user_mailbox(username, domain, mail_dir):
        print(f"Creating mailbox for {username}@{domain}.")
        if not create_user_mailbox(username, domain, mail_dir):
            return False
    else:
        print(f"Mailbox for {username}@{domain} already exists.")
    if not run_postmap(domain_file, mailbox_map_file):
        print("Failed to run postmap.")
        return False
    print(f"Running postmap on {domain_file} and {mailbox_map_file} completed successfully.")
    print(f"User {username}@{domain} created successfully.")
    return True


if __name__ == "__main__":
    cli.parse_and_call()
