# v1.0 Tentative Roadmap

Below are some forward looking features to help improve usage.

## Self hosting (Complete)

The project can live in its own git repo served over http.

## Git hosting and test (Partial, Tests needed)

Store the git repos on the host and automate testing of git clone, commit, push

## Improved CI and project setup (v0.5 complete)

Improvements to the CI process, allowing the project dependencies to be
installed, tests run and services started without unnecessary steps or
boilerplate.

## Reduce container restarts on upgrade

Container restarts cause downtime. Where possible move to actions and
configuration that don't require a container restart. Maybe configuration is
editable over webdav, and only a `httpd -k graceful` configuration is needed?
Consider more options to reduce downtime and improve the upgrade experience.

## Harmonize host side FSTree and Dockerfile directories

The FSTree should be the source of truth from which the directory structure is
rendered both on the host and in the container to keep cognitive load down and
make it easier to reason about what's going on in the system.

## User logs and action logs

User logging is the typical logging that you'd expect, a message with different
logging levels.

Action logs are program parsable, so that a program can reproduce the same
sequence of side-effects. These are helpful for generating new types of tests
from known states and reproducing states across a network with two different
instances of the process.

## Isolated tests

Many of the tests could be improved by not having them depend on a pre-existing
state. Each test should be isolated so that it can work without depending on
another test having been run.

## Test coverage

Improve test coverage by reducing the reliance of external services to exercise
the code paths.
