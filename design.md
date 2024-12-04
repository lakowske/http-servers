# http-server Design

The following design guidelines informs development on the rules and
expectations for managing configuration, IoC, and any other constructions that
may occur during the development of the project. Each guideline includes
motivations for the the guideline. The guidelines aren't arbitrary, but come
from multiple interations of developing the same functionality, learning what
works and what does not along the way.

## Configuration

The heart of the project is a configuration tree that user's can update from CLI
arguments, yaml configuration files and json http requests. The goal is to
reduce the cognitive load by placing all configuration in one place.

## Constants

Constants are provided for string values often referenced in the program. The
principle is to relying on the IDE to help autocomplete common constants and
ensure consistent usage of constants.

## Services

Services can be used without specifying or carrying over details from the Config
tree. Calling service functionality should be concise, allowing procedure to be
made clear without forcing the user to resupply or overspecify configuration
details, which makes the reading of a list of procedures.

## Task Dependencies

Actions and effects can be placed in a dependency tree, so that the dependency
is made explicit. The ability to request, or generate a dependency using a
dependency tree increases the chances that large integrations can be tested and
reproduced successfully.

## Late binding

Configuration of services is late bound, meaning that services are not
instantiated with configuration at startup. It's only when a service is
requested that the configuration is bound to a service. Some services are
rebound each time (i.e. are Factory provided service) and some are bound once (
Singleton services).
