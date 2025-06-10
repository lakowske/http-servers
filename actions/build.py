"""
Can do the following actions:
1. Renders the configuration tree into a build directory
2. Builds the image using the build directory
3. Runs the container
4. Does a health check on the container
5. Runs certbot to get a certificates from Let's Encrypt
6. Reloads the configuration

"""

import os
import json
from datetime import datetime
import uvicorn
from http_server.health_check import healthcheck
from actions.shell import ipython_shell
from actions.dynamic_cli import DynamicCLI
from configuration.tree_walker import TreeRenderer
from configuration.container import ServerContainer
from services.httpd_service import (
    LATEST_IMAGE,
    DEFAULT_HTTPD_CONTAINER_NAME,
    GIT_REPO_VOLUME,
    GIT_TEST_REPO,
    WEBDAV_VOLUME,
)
from services.mail_service import (
    LATEST_IMAGE as MAIL_LATEST_IMAGE,
    DEFAULT_MAIL_CONTAINER_NAME,
    MAIL_VOLUME,
)


cli = DynamicCLI()

container = ServerContainer()
config_service = container.config_service()
config_service.load_yaml_config("secrets/config.yaml")
podman_service = container.podman_service()
httpd_service = container.httpd_service()
mail_service = container.mail_service()
user_service = container.user_service()


def save_build_log(image_name: str, build_output: list, success: bool = True, error_msg: str = None):
    """
    Save build logs to a timestamped file for debugging and tracking
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    status = "SUCCESS" if success else "FAILED"
    log_filename = f"logs/{image_name}_{timestamp}_{status}.log"
    
    # Ensure logs directory exists
    os.makedirs("logs", exist_ok=True)
    
    log_data = {
        "timestamp": timestamp,
        "image_name": image_name,
        "status": status,
        "error_message": error_msg,
        "build_output": []
    }
    
    # Process build output - handle both bytes and strings
    for line in build_output:
        if isinstance(line, bytes):
            try:
                # Try to parse as JSON first (common for Docker/Podman output)
                json_line = json.loads(line.decode('utf-8'))
                if 'stream' in json_line:
                    log_data["build_output"].append(json_line['stream'].strip())
                else:
                    log_data["build_output"].append(str(json_line))
            except (json.JSONDecodeError, UnicodeDecodeError):
                # Fall back to simple string representation
                log_data["build_output"].append(line.decode('utf-8', errors='replace').strip())
        else:
            log_data["build_output"].append(str(line).strip())
    
    # Save both JSON (structured) and plain text (readable) versions
    with open(log_filename, 'w', encoding='utf-8') as f:
        json.dump(log_data, f, indent=2, ensure_ascii=False)
    
    # Also save a human-readable version
    readable_filename = log_filename.replace('.log', '_readable.log')
    with open(readable_filename, 'w', encoding='utf-8') as f:
        f.write(f"=== BUILD LOG FOR {image_name} ===\n")
        f.write(f"Timestamp: {timestamp}\n")
        f.write(f"Status: {status}\n")
        if error_msg:
            f.write(f"Error: {error_msg}\n")
        f.write(f"{'='*50}\n\n")
        
        for line in log_data["build_output"]:
            if line.strip():  # Skip empty lines
                f.write(f"{line}\n")
    
    print(f"Build log saved to: {log_filename}")
    print(f"Readable log saved to: {readable_filename}")
    return log_filename


@cli.register()
def list_containers():
    """
    List all containers
    """
    containers = podman_service.list_containers()
    for podman_container in containers:
        print(f'{podman_container.name} {podman_container.attrs["State"]}')
    return containers


@cli.register()
def render():
    """
    Render the configuration tree into a build directory
    """
    walker = TreeRenderer()
    walker.walk(config_service.config.build_paths, config_service.config)


@cli.register()
def build_images():
    """
    Build the image using the configuration found in secrets/config.yaml
    """
    # Build httpd image
    build_httpd_image()
    # Build mail image
    build_mail_image()


@cli.register()
def build_httpd_image():
    """
    Build the httpd image using the configuration found in secrets/config.yaml
    """
    try:
        image_id, build_output = httpd_service.build_image(LATEST_IMAGE)
        assert image_id is not None
        
        # Save build logs
        save_build_log("httpd-nexus", build_output, success=True)
        
        # Still print output to console for immediate feedback
        for line in build_output:
            print(line)
        return image_id
    except Exception as e:
        error_msg = str(e)
        print(f"Build failed: {error_msg}")
        # Save failed build log if we have partial output
        if 'build_output' in locals():
            save_build_log("httpd-nexus", build_output, success=False, error_msg=error_msg)
        else:
            save_build_log("httpd-nexus", [], success=False, error_msg=error_msg)
        raise


@cli.register()
def build_mail_image():
    """
    Build the mail image using the configuration found in secrets/config.yaml
    """
    try:
        image_id, build_output = mail_service.build_image(MAIL_LATEST_IMAGE)
        assert image_id is not None
        
        # Save build logs
        save_build_log("mail-nexus", build_output, success=True)
        
        # Still print output to console for immediate feedback
        for line in build_output:
            print(line)
        return image_id
    except Exception as e:
        error_msg = str(e)
        print(f"Build failed: {error_msg}")
        # Save failed build log if we have partial output
        if 'build_output' in locals():
            save_build_log("mail-nexus", build_output, success=False, error_msg=error_msg)
        else:
            save_build_log("mail-nexus", [], success=False, error_msg=error_msg)
        raise


@cli.register()
def build():
    """
    Build the image using the configuration found in secrets/config.yaml
    """
    render()
    build_images()


@cli.register()
def run_httpd_container():
    """
    Run the container using the image built in the build step
    """
    httpd_container = httpd_service.run_container(LATEST_IMAGE, DEFAULT_HTTPD_CONTAINER_NAME)
    assert httpd_container is not None
    assert httpd_service.is_container_running(httpd_container.id)


@cli.register()
def run_mail_container():
    """
    Run the mail container using the image built in the build step
    """
    mail_container = mail_service.run_container(MAIL_LATEST_IMAGE, DEFAULT_MAIL_CONTAINER_NAME)
    assert mail_container is not None
    assert mail_service.is_container_running(mail_container.id)


@cli.register()
def health():
    """
    Check the health of the container
    """
    domain = config_service.config.admin.domain
    assert healthcheck(domain)


@cli.register()
def certificates():
    """
    Get certificates from Let's Encrypt
    """
    certbot = container.certbot_service()
    success = certbot.create_certificate(config_service.config.admin.domain, dry_run=False, staging=False)
    assert success is True


@cli.register()
def reload_httpd():
    """
    Reload the http server configuration
    """
    container_id = httpd_service.get_container_id(DEFAULT_HTTPD_CONTAINER_NAME)
    assert container_id is not None
    httpd_service.reload_configuration(container_id)
    assert httpd_service.is_container_running(container_id)


@cli.register()
def create_mail_volume():
    """
    Create a mail volume
    """
    mail_service.create_mail_volume(MAIL_VOLUME)


@cli.register()
def remove_mail_volume():
    """
    Remove the mail volume
    """
    mail_service.remove_mail_volume(MAIL_VOLUME)


@cli.register()
def create_git_repo_volume():
    """
    Create a git repo volume
    """
    httpd_service.create_repo_volume(GIT_REPO_VOLUME)


@cli.register()
def remove_git_repo_volume():
    """
    Remove the git repo volume
    """
    httpd_service.remove_repo_volume(GIT_REPO_VOLUME)


@cli.register()
def create_webdav_volume():
    """
    Create a webdav volume
    """
    httpd_service.create_repo_volume(WEBDAV_VOLUME)


@cli.register()
def remove_webdav_volume():
    """
    Remove the webdav volume
    """
    httpd_service.remove_repo_volume(WEBDAV_VOLUME)


@cli.register()
def create_test_repo():
    """
    Create a test git repo
    """
    container_id = httpd_service.get_container_id(DEFAULT_HTTPD_CONTAINER_NAME)
    assert container_id is not None
    httpd_service.create_git_repo(container_id, GIT_TEST_REPO)


@cli.register()
def reload():
    """
    Reload the configuration
    """
    certbot = container.certbot_service()
    success = certbot.update_apache_configs_to_letsencrypt(config_service.config.admin.domain)
    assert success
    container_id = httpd_service.get_container_id(DEFAULT_HTTPD_CONTAINER_NAME)
    assert container_id is not None
    httpd_service.reload_configuration(container_id)
    assert httpd_service.is_container_running(container_id)


@cli.register()
def rm_httpd_container():
    """
    Remove the container
    """
    container_id = httpd_service.get_container_id(DEFAULT_HTTPD_CONTAINER_NAME)
    assert container_id is not None
    if httpd_service.is_container_running(container_id):
        httpd_service.stop_container(container_id)
    httpd_service.remove_container(container_id)
    container_id = httpd_service.get_container_id(DEFAULT_HTTPD_CONTAINER_NAME)
    assert container_id is None


@cli.register()
def rm_mail_container():
    """
    Remove the mail container
    """
    container_id = mail_service.get_container_id(DEFAULT_MAIL_CONTAINER_NAME)
    assert container_id is not None
    if mail_service.is_container_running(container_id):
        mail_service.stop_container(container_id)
    mail_service.remove_container(container_id)
    container_id = mail_service.get_container_id(DEFAULT_MAIL_CONTAINER_NAME)
    assert container_id is None


@cli.register()
def rm_httpd_image():
    """
    Remove the httpd image
    """
    image = LATEST_IMAGE
    httpd_service.remove_image(image)
    assert httpd_service.get_image_id(image) is None


@cli.register()
def rm_mail_image():
    """
    Remove the mail image
    """
    image = MAIL_LATEST_IMAGE
    mail_service.remove_image(image)
    assert mail_service.get_image_id(image) is None


@cli.register()
def git_password():
    """
    Generate a new password
    """
    password = user_service.random_password("git")
    print(password)
    return password


@cli.register()
def run_ops():
    """
    Run the operations http server.
    """
    uvicorn.run(
        "web.home:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
        reload_dirs=["./templates", "./templates/web"],
        reload_includes=["*.html"],
    )


@cli.register()
def run_shell():
    """
    Run an IPython shell
    """
    ipython_shell()


@cli.register()
def list_build_logs():
    """
    List all available build logs
    """
    if not os.path.exists("logs"):
        print("No logs directory found. No builds have been logged yet.")
        return
    
    log_files = [f for f in os.listdir("logs") if f.endswith('.log') and not f.endswith('_readable.log')]
    
    if not log_files:
        print("No build logs found.")
        return
    
    print("Available build logs:")
    print("-" * 50)
    
    # Group logs by image and sort by timestamp
    logs_by_image = {}
    for log_file in log_files:
        parts = log_file.split('_')
        if len(parts) >= 3:
            image = parts[0]
            timestamp = parts[1] + '_' + parts[2]
            status = parts[3].replace('.log', '')
            
            if image not in logs_by_image:
                logs_by_image[image] = []
            logs_by_image[image].append({
                'file': log_file,
                'timestamp': timestamp,
                'status': status
            })
    
    for image, logs in logs_by_image.items():
        print(f"\n{image}:")
        for log in sorted(logs, key=lambda x: x['timestamp'], reverse=True):
            status_icon = "✅" if log['status'] == "SUCCESS" else "❌"
            print(f"  {status_icon} {log['timestamp']} ({log['status']}) - {log['file']}")


@cli.register()
def view_build_log():
    """
    View a specific build log (will show latest if no specific log provided)
    """
    if not os.path.exists("logs"):
        print("No logs directory found.")
        return
    
    log_files = [f for f in os.listdir("logs") if f.endswith('_readable.log')]
    
    if not log_files:
        print("No readable build logs found.")
        return
    
    # Get the most recent log
    latest_log = max(log_files, key=lambda f: os.path.getctime(os.path.join("logs", f)))
    
    print(f"Showing latest build log: {latest_log}")
    print("=" * 60)
    
    with open(os.path.join("logs", latest_log), 'r', encoding='utf-8') as f:
        content = f.read()
        # Limit output to last 100 lines for readability
        lines = content.split('\n')
        if len(lines) > 100:
            print("... (showing last 100 lines) ...")
            lines = lines[-100:]
        print('\n'.join(lines))


@cli.register()
def clean_build_logs():
    """
    Clean up old build logs (keeps last 10 logs per image)
    """
    if not os.path.exists("logs"):
        print("No logs directory found.")
        return
    
    log_files = [f for f in os.listdir("logs") if f.endswith('.log')]
    
    if not log_files:
        print("No build logs to clean.")
        return
    
    # Group by image type
    logs_by_image = {}
    for log_file in log_files:
        parts = log_file.split('_')
        if len(parts) >= 3:
            image = parts[0]
            if image not in logs_by_image:
                logs_by_image[image] = []
            logs_by_image[image].append(log_file)
    
    removed_count = 0
    for image, logs in logs_by_image.items():
        # Sort by modification time (newest first)
        logs.sort(key=lambda f: os.path.getmtime(os.path.join("logs", f)), reverse=True)
        
        # Keep only the 10 most recent logs
        logs_to_remove = logs[10:]  # Remove all but first 10
        
        for log_file in logs_to_remove:
            log_path = os.path.join("logs", log_file)
            os.remove(log_path)
            removed_count += 1
            
            # Also remove corresponding readable log
            readable_file = log_file.replace('.log', '_readable.log')
            readable_path = os.path.join("logs", readable_file)
            if os.path.exists(readable_path):
                os.remove(readable_path)
                removed_count += 1
    
    print(f"Cleaned up {removed_count} old log files. Kept 10 most recent logs per image.")


@cli.register()
def start():
    """
    Complete startup sequence: render configs, build images, create volumes, and start both containers
    """
    print("Starting complete system startup...")
    render()
    build_images()
    create_git_repo_volume()
    create_mail_volume()
    create_webdav_volume()
    run_httpd_container()
    run_mail_container()
    print("System startup complete!")


@cli.register()
def stop():
    """
    Stop both HTTP and mail containers
    """
    print("Stopping all containers...")
    try:
        rm_httpd_container()
        print("HTTP container stopped")
    except Exception as e:
        print(f"HTTP container stop failed or already stopped: {e}")
    
    try:
        rm_mail_container()
        print("Mail container stopped")
    except Exception as e:
        print(f"Mail container stop failed or already stopped: {e}")
    
    print("All containers stopped!")


@cli.register()
def restart():
    """
    Restart both HTTP and mail containers with fresh builds
    """
    print("Restarting system with fresh builds...")
    stop()
    render()
    build_images()
    run_httpd_container()
    run_mail_container()
    print("System restart complete!")


@cli.register()
def status():
    """
    Show comprehensive status of all services, containers, and volumes
    """
    print("=== System Status ===")
    
    print("\n--- Containers ---")
    list_containers()
    
    print("\n--- HTTP Service ---")
    try:
        container_id = httpd_service.get_container_id(DEFAULT_HTTPD_CONTAINER_NAME)
        if container_id:
            running = httpd_service.is_container_running(container_id)
            print(f"HTTP Container: {'Running' if running else 'Stopped'} (ID: {container_id[:12]})")
        else:
            print("HTTP Container: Not found")
    except Exception as e:
        print(f"HTTP Container: Error checking status - {e}")
    
    print("\n--- Mail Service ---")
    try:
        container_id = mail_service.get_container_id(DEFAULT_MAIL_CONTAINER_NAME)
        if container_id:
            running = mail_service.is_container_running(container_id)
            print(f"Mail Container: {'Running' if running else 'Stopped'} (ID: {container_id[:12]})")
        else:
            print("Mail Container: Not found")
    except Exception as e:
        print(f"Mail Container: Error checking status - {e}")
    
    print("\n--- Images ---")
    try:
        httpd_image_id = httpd_service.get_image_id(LATEST_IMAGE)
        print(f"HTTP Image: {'Available' if httpd_image_id else 'Not built'}")
        
        mail_image_id = mail_service.get_image_id(MAIL_LATEST_IMAGE)
        print(f"Mail Image: {'Available' if mail_image_id else 'Not built'}")
    except Exception as e:
        print(f"Images: Error checking status - {e}")
    
    print("\n--- Health Check ---")
    try:
        domain = config_service.config.admin.domain
        healthy = healthcheck(domain)
        print(f"HTTP Health: {'OK' if healthy else 'Failed'}")
    except Exception as e:
        print(f"HTTP Health: Error - {e}")


@cli.register()
def clean():
    """
    Clean up all containers, images, and volumes (destructive operation)
    """
    print("WARNING: This will remove all containers, images, and volumes!")
    response = input("Are you sure? Type 'yes' to continue: ")
    if response.lower() != 'yes':
        print("Operation cancelled")
        return
    
    print("Cleaning up system...")
    
    # Stop and remove containers
    try:
        rm_httpd_container()
        print("HTTP container removed")
    except Exception as e:
        print(f"HTTP container removal failed: {e}")
    
    try:
        rm_mail_container()
        print("Mail container removed")
    except Exception as e:
        print(f"Mail container removal failed: {e}")
    
    # Remove images
    try:
        rm_httpd_image()
        print("HTTP image removed")
    except Exception as e:
        print(f"HTTP image removal failed: {e}")
    
    try:
        rm_mail_image()
        print("Mail image removed")
    except Exception as e:
        print(f"Mail image removal failed: {e}")
    
    # Remove volumes
    try:
        remove_git_repo_volume()
        print("Git repo volume removed")
    except Exception as e:
        print(f"Git repo volume removal failed: {e}")
    
    try:
        remove_mail_volume()
        print("Mail volume removed")
    except Exception as e:
        print(f"Mail volume removal failed: {e}")
    
    try:
        remove_webdav_volume()
        print("WebDAV volume removed")
    except Exception as e:
        print(f"WebDAV volume removal failed: {e}")
    
    print("System cleanup complete!")


if __name__ == "__main__":
    cli.parse_and_call()
