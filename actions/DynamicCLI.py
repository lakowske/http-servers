#!/usr/bin/env python3
"""
DynamicCLI.py
A dynamic command-line interface (CLI) that allows you to register functions
and call them from the command line or via a REST API. It automatically
generates argument parsers based on function signatures and type hints.
You can also enable a REST API to call these functions over HTTP.
It supports type conversion, default values, and required parameters.
"""

import argparse
import sys
import inspect
import json
import threading
import time
from typing import Any, Dict, Callable, get_type_hints
from flask import Flask, request, jsonify


class DynamicCLI:
    """
    A dynamic command-line interface (CLI) that allows you to register functions
    and call them from the command line or via a REST API. It automatically
    generates argument parsers based on function signatures and type hints.
    You can also enable a REST API to call these functions over HTTP.
    """

    def __init__(self, enable_rest_api=False, host="localhost", port=5000):
        self.functions = {}
        self.enable_rest_api = enable_rest_api
        self.host = host
        self.port = port
        self.app = None
        if enable_rest_api:
            self._setup_flask_app()

    def register_function(self, func: Callable):
        """Register a function to be callable from CLI and REST API"""
        self.functions[func.__name__] = func
        return func

    def register(self, name: str = None):
        """Decorator to register functions"""

        def decorator(func):
            func_name = name or func.__name__
            self.functions[func_name] = func
            return func

        return decorator

    def _setup_flask_app(self):
        """Setup Flask app for REST API"""
        self.app = Flask(__name__)

        @self.app.route("/functions", methods=["GET"])
        def list_functions():
            """List all available functions and their signatures"""
            functions_info = {}
            for func_name, func in self.functions.items():
                sig_info = self._get_function_signature(func)
                doc = func.__doc__ or "No description available"
                functions_info[func_name] = {
                    "description": doc.strip(),
                    "parameters": sig_info,
                }
            return jsonify(functions_info)

        @self.app.route("/call/<function_name>", methods=["POST"])
        def call_function(function_name):
            """Call a function via REST API"""
            if function_name not in self.functions:
                return (
                    jsonify(
                        {
                            "error": f'Function "{function_name}" not found',
                            "available_functions": list(self.functions.keys()),
                        }
                    ),
                    404,
                )

            func = self.functions[function_name]
            func_params = self._get_function_signature(func)

            # Get JSON data from request
            try:
                data = request.get_json() or {}
            except Exception as e:
                return jsonify({"error": f"Invalid JSON: {str(e)}"}), 400

            # Validate and convert parameters
            kwargs = {}
            errors = []

            for param_name, param_info in func_params.items():
                if param_name in data:
                    try:
                        converted_value = self._convert_value(data[param_name], param_info["type"])
                        kwargs[param_name] = converted_value
                    except (ValueError, TypeError) as e:
                        errors.append(f"Parameter '{param_name}': {str(e)}")
                elif param_info["required"]:
                    errors.append(f"Missing required parameter: '{param_name}'")
                else:
                    kwargs[param_name] = param_info["default"]

            if errors:
                return (
                    jsonify(
                        {
                            "error": "Parameter validation failed",
                            "details": errors,
                            "expected_parameters": func_params,
                        }
                    ),
                    400,
                )

            # Call the function
            try:
                result = func(**kwargs)
                return jsonify(
                    {
                        "success": True,
                        "function": function_name,
                        "parameters": kwargs,
                        "result": result,
                    }
                )
            except Exception as e:
                return (
                    jsonify(
                        {
                            "error": f"Function execution failed: {str(e)}",
                            "function": function_name,
                            "parameters": kwargs,
                        }
                    ),
                    500,
                )

        @self.app.route("/health", methods=["GET"])
        def health_check():
            """Health check endpoint"""
            return jsonify(
                {
                    "status": "healthy",
                    "functions_count": len(self.functions),
                    "timestamp": time.time(),
                }
            )

    def _get_function_signature(self, func: Callable) -> Dict[str, Any]:
        """Extract function signature information"""
        sig = inspect.signature(func)
        type_hints = get_type_hints(func)

        params = {}
        for param_name, param in sig.parameters.items():
            param_type = type_hints.get(param_name, str)
            param_info = {
                "required": param.default == inspect.Parameter.empty,
                "default": (param.default if param.default != inspect.Parameter.empty else None),
                "type": (param_type.__name__ if hasattr(param_type, "__name__") else str(param_type)),
            }
            params[param_name] = param_info

        return params

    def _convert_value(self, value: Any, target_type: type):
        """Convert value to target type"""
        if value is None:
            return None

        # If value is already the correct type, return as-is
        if isinstance(value, target_type):
            return value

        if target_type == bool:
            if isinstance(value, str):
                return value.lower() in ("true", "1", "yes", "on")
            return bool(value)
        elif target_type == int:
            return int(float(value))  # Handle "5.0" -> 5
        elif target_type == float:
            return float(value)
        elif target_type == list:
            if isinstance(value, str):
                return value.split(",") if value else []
            elif isinstance(value, list):
                return value
            else:
                return [value]
        else:
            return str(value)

    def start_rest_api(self, debug=False, threaded=True):
        """Start the REST API server"""
        if not self.app:
            raise RuntimeError("REST API not enabled. Set enable_rest_api=True when creating DynamicCLI instance.")

        print(f"Starting REST API server on {self.host}:{self.port}")
        print("Available endpoints:")
        print(f"  GET  http://{self.host}:{self.port}/functions - List all functions")
        print(f"  POST http://{self.host}:{self.port}/call/<function_name> - Call a function")
        print(f"  GET  http://{self.host}:{self.port}/health - Health check")
        print()

        if threaded:
            server_thread = threading.Thread(target=lambda: self.app.run(host=self.host, port=self.port, debug=debug))
            server_thread.daemon = True
            server_thread.start()
            return server_thread
        else:
            self.app.run(host=self.host, port=self.port, debug=debug)

    def parse_and_call(self, args=None):
        """Parse command line arguments and call the specified function"""
        if args is None:
            args = sys.argv[1:]

        # Special command to start REST API server
        if args and args[0] == "--start-api":
            if not self.enable_rest_api:
                print("Error: REST API not enabled. Create instance with enable_rest_api=True")
                return
            self.start_rest_api(debug="--debug" in args)
            return

        if not args:
            print("Available functions:")
            for func_name in self.functions.keys():
                print(f"  {func_name}")
            if self.enable_rest_api:
                print(f"\nREST API available. Use: python {sys.argv[0]} --start-api")
            return

        function_name = args[0]

        if function_name not in self.functions:
            print(f"Error: Function '{function_name}' not found.")
            print("Available functions:")
            for func_name in self.functions.keys():
                print(f"  {func_name}")
            return

        func = self.functions[function_name]
        func_params = self._get_function_signature(func)

        # Create argument parser for this specific function
        parser = argparse.ArgumentParser(
            description=f"Call function: {function_name}",
            prog=f"{sys.argv[0]} {function_name}",
        )

        # Add arguments based on function signature
        for param_name, param_info in func_params.items():
            arg_name = f"--{param_name}"

            if param_info["required"]:
                parser.add_argument(
                    arg_name,
                    required=True,
                    type=str,
                    help=f"Required parameter: {param_name} ({param_info['type']})",
                )
            else:
                parser.add_argument(
                    arg_name,
                    default=param_info["default"],
                    type=str,
                    help=f"Optional parameter: {param_name} ({param_info['type']}, default: {param_info['default']})",
                )

        # Parse the remaining arguments
        try:
            parsed_args = parser.parse_args(args[1:])
        except SystemExit:
            return

        # Convert arguments to proper types and prepare function call
        kwargs = {}
        for param_name, param_info in func_params.items():
            value = getattr(parsed_args, param_name)
            if value is not None:
                try:
                    # Get the actual type from type hints
                    type_hints = get_type_hints(func)
                    target_type = type_hints.get(param_name, str)
                    converted_value = self._convert_value(value, target_type)
                    kwargs[param_name] = converted_value
                except (ValueError, TypeError) as e:
                    print(f"Error converting {param_name}={value} to {param_info['type']}: {e}")
                    return

        # Call the function
        try:
            result = func(**kwargs)
            if result is not None:
                print(result)
        except Exception as e:
            print(f"Error calling {function_name}: {e}")


# Example usage
if __name__ == "__main__":
    # Create CLI instance with REST API enabled
    cli = DynamicCLI(enable_rest_api=True, host="localhost", port=5000)

    # Example functions to register
    @cli.register()
    def greet(name: str, greeting: str = "Hello", times: int = 1):
        """Greet someone multiple times"""
        messages = []
        for _ in range(times):
            message = f"{greeting}, {name}!"
            messages.append(message)
        return messages

    @cli.register()
    def calculate(operation: str, a: float, b: float):
        """Perform basic calculations"""
        operations = {
            "add": lambda x, y: x + y,
            "subtract": lambda x, y: x - y,
            "multiply": lambda x, y: x * y,
            "divide": lambda x, y: (x / y if y != 0 else "Cannot divide by zero"),
        }

        if operation not in operations:
            raise ValueError(f"Unknown operation: {operation}. Available: {list(operations.keys())}")

        result = operations[operation](a, b)
        return {"operation": operation, "operands": [a, b], "result": result}

    @cli.register()
    def process_list(items: list, action: str = "count"):
        """Process a list of items"""
        if action == "count":
            return {"action": action, "count": len(items), "items": items}
        elif action == "sort":
            return {"action": action, "result": sorted(items)}
        elif action == "reverse":
            return {"action": action, "result": items[::-1]}
        else:
            raise ValueError(f"Unknown action: {action}")

    @cli.register("user_info")
    def show_user_info(user: str, age: int = None, active: bool = True):
        """Display user information"""
        info = {"user": user, "active": active}
        if age is not None:
            info["age"] = age
        return info

    # Parse and execute
    cli.parse_and_call()

# CLI Usage Examples:
# python script.py greet --name Alice
# python script.py calculate --operation add --a 5 --b 3
# python script.py --start-api

# REST API Usage Examples:
# curl -X GET http://localhost:5000/functions
# curl -X POST http://localhost:5000/call/greet -H "Content-Type: application/json" -d '{"name": "Alice", "times": 2}'
# curl -X POST http://localhost:5000/call/calculate \
# -H "Content-Type: application/json" -d '{"operation": "add", "a": 5.5, "b": 3.2}'
# curl -X POST http://localhost:5000/call/process_list \
# -H "Content-Type: application/json" -d '{"items": ["apple", "banana", "cherry"], "action": "sort"}'
