# Podman Playbook for Debian/Ubuntu

This playbook describes how to set up and use `podman` with `systemd` and `loginctl` to allow a lingering `podman` service on a Debian/Ubuntu box.

## Prerequisites

1. Ensure your system is up-to-date:

    ```sh
    sudo apt update
    sudo apt upgrade -y
    ```

2. Install `podman`:

    ```sh
    sudo apt install -y podman
    ```

## Setting Up Podman with Systemd

### 1. Create a Systemd Service for Podman

Create a systemd service file for your `podman` container. For example, create a file named `~/.config/systemd/user/apache-container.service`:

```ini
[Unit]
Description=Apache Container Service
Wants=network-online.target
After=network-online.target

[Service]
Type=exec
ExecStartPre=-/usr/bin/podman stop apache
ExecStartPre=-/usr/bin/podman rm apache
ExecStart=/usr/bin/podman run \
    --name apache \
    -p 80:80 \
    -p 443:443 \
    --rm \
    docker.io/library/httpd:latest
ExecStop=/usr/bin/podman stop apache
Restart=on-failure
RestartSec=30

[Install]
WantedBy=default.target
```

### 2. Enable and Start the Service

Enable and start the systemd service:

```sh
sudo systemctl enable apache-container.service
sudo systemctl start apache-container.service
```

### 3. Verify the Service

Check the status of the service to ensure it is running:

```sh
sudo systemctl status podman-container.service
```

## Using loginctl to Allow Lingering

### 1. Enabling Lingering for Your User

Allow lingering for your user to enable the service to run even after you log out:

```sh
sudo loginctl enable-linger $USER
```

### 2. Verify Lingering

verify that lingering is enable for your user:

```sh
loginctl show-user $USER | grep Linger
```

The output should show ```Linger=yes```.

## Conclusion

You have successfully set up `podman` with `systemd` and `loginctl` to allow a lingering `podman` service on a Debian/Ubuntu box. You can now manage your `podman` containers using systemd and ensure they continue running even after you log out.

This playbook provides step-by-step instructions for setting up and using `podman` with `systemd` and `loginctl` on a Debian/Ubuntu system. It covers creating systemd service files, enabling lingering for your user, and managing `podman` containers with systemd.
