# v1.0 Tentative Roadmap

Below are some forward looking features to help improve usage.

## Self hosting

The project can live in its own git repo served over http.

## Git hosting and test

Store the git repos on the host and automate testing of git clone, commit, push

## User logs and action logs

User logging is the typical logging that you'd expect, a message with different
logging levels.

Action logs are program parsable, so that a program can reproduce the same
sequence of side-effects. These are helpful for generating new types of tests
from known states and reproducing states across a network with two different
instances of the process.

## Improved CI and project setup

Improvements to the CI process, allowing the project dependencies to be
installed, tests run and services started without unnecessary steps or
boilerplate.

## Isolated tests

Many of the tests could be improved by not having them depend on a pre-existing
state. Each test should be isolated so that it can work without depending on
another test having been run.

## Test coverage

Improve test coverage by reducing the reliance of external services to exercise
the code paths.
