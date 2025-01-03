# Http Server

![Build Status](https://github.com/lakowske/http-servers/actions/workflows/python-app.yml/badge.svg)

## Outline

1. [Introduction](#introduction)
2. [Purpose](#purpose)
3. [Strategy](#strategy)
4. [Installation](#installation)
5. [Usage](#usage)
6. [Testing](#testing)
7. [Contributing](#contributing)
8. [License](#license)

## Introduction

The project is meant to act as an http entrypoint to projects that I'm running.
There's a persistent need to serve stateful services, preferably without
incurring excessive costs or overreliance on external providers whose
conditions, proprietary protocols and availability are outside my control. The
idea is to use off the shelf tools and protocols to minimize work and
maintenance while maximizing my compatibility with common internet
infrastructure.

## Purpose

The purpose is to allow secure access controlled access to services over https.
There is a need for private Git access over https. There is also a need to route
traffic to backing services using https while reducing the IP/DNS space
required, keeping server cost and complexity to a minimum. There is a need to
manage users and access to Git and reverse proxied services. This should be
accomplished without reliance on extraneous external service providers.

## Strategy

Use a containerized web server to provide https, reverse proxy, cgi and other
common modes (e.g. Apache or possibly Nginx). Create configuration of the
container using Python tooling and unit test using Python testing framework.
Python comes with batteries included, so it works well for glueing together
configuration, apis and the runtime tooling used in the project. The workflow
should allow for multiple branches to run on the same host to test new
approaches while allowing existing services to continue to run without
interruption. The aspiration is toward blue green deployment of components of
the system, to ease changes to services as they occur without disruption. To
aide in this, reverse proxy configuration should be able to be updated without
restarting the reverse proxy and severing existing connections.

## Installation

Configure secrets/config.yaml with your domain and address. These will be needed
for Let's Encrypt certificates to work properly.

```yaml
admin:
  domain: "example.com"
  email: "admin@example.com"
```

### Run

```bash
# Setup your python and shell environment.  Creates an alias now=python actions/build.py
source project.sh
# Build the configuration build/ dir and container image
now build
# Create the git repo
now create_git_repo_volume
# Run the container, storing git repos in the git repo volume
now run_container
# Create the git test repo, if you want to do integration testing
now create_test_repo
# Create the let's encrypt certificates
now certificates
# Reload the httpd configuration to use the certificates
now reload
```

## Usage

Once you've built the container and configured it, you can visit your domain's
https endpoint to access documents and git repositories.

## Testing

Describe how to run tests for the project. Include any setup or dependencies
required for testing.

## Contributing

Provide guidelines for contributing to the project. This can include coding
standards, pull request guidelines, and any other relevant information.

## License

Specify the license under which the project is distributed.
