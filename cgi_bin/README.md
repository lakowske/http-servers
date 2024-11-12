# CGI_BIN

This directory can be mounted directly in a web server like Apache to serve
cgi-bin scripts/programs.

## Mounting in Apache

To mount this directory in an Apache debian/ubuntu install, follow these steps:

1. **Ensure the `cgi` or `cgid` module is enabled**:
   ```bash
   sudo a2enmod cgi
   sudo systemctl restart apache2
   ```

2. **Update your Apache configuration**: Add the following configuration to your
   Apache configuration file (e.g.,
   `/etc/apache2/sites-available/000-default.conf`):
   ```apache
   <Directory "/path/to/your/cgi-bin">
       AllowOverride None
       Options +ExecCGI
       Require all granted
   </Directory>

   ScriptAlias /cgi-bin/ "/path/to/your/cgi-bin/"
   ```

3. **Restart Apache**:
   ```bash
   sudo systemctl restart apache2
   ```

## Mounting in Apache httpd podman container

The mount point is already configured. You can verify the build/apache
configuration to ensure that the mod_cgi module is enabled and the cgi-bin
directory is configured, but normally you can simply drop executables in this
directory and run the container.

## Testing Scripts Locally

To test scripts locally without a web server, you can use the `cgi-fcgi` tool:

1. **Install `cgi-fcgi`**:
   ```bash
   sudo apt-get install fcgiwrap
   ```

2. **Run your CGI script**:
   ```bash
   SCRIPT_FILENAME=/path/to/your/cgi-bin/script.cgi REQUEST_METHOD=GET cgi-fcgi -bind -connect /var/run/fcgiwrap.socket
   ```

Replace `/path/to/your/cgi-bin` with the actual path to your `cgi-bin`
directory.

By following these steps, you can either mount the `cgi-bin` directory in an
Apache HTTPD container or test your CGI scripts locally.
