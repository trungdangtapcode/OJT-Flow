"""Core domain contracts and policies.

The core package is intentionally framework-free. It may use Pydantic for typed
contracts, but it must not import FastAPI, storage adapters, cloud SDKs, model
providers, or MCP runtimes.
"""

