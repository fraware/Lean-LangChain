"""Contract tests: operation catalog, MCP tool list, and Python SDK stay in parity.

Ensures a single operation added to the catalog is reflected in MCP tools and SDK client.
"""

from __future__ import annotations

from lean_langchain_schemas.operation_catalog import (
    OPERATIONS,
    build_mcp_tool_schemas,
    get_mcp_tool_name,
)


def test_operation_catalog_mcp_tool_schemas_parity() -> None:
    """MCP tool list built from catalog has one entry per operation and names match."""
    schemas = build_mcp_tool_schemas()
    assert len(schemas) == len(OPERATIONS)
    catalog_names = {get_mcp_tool_name(op["name"]) for op in OPERATIONS}
    schema_names = {s["name"] for s in schemas}
    assert schema_names == catalog_names


def test_mcp_tools_dict_matches_catalog() -> None:
    """build_mcp_tools returns exactly the tool names from the operation catalog."""
    from lean_langchain_sdk.client import ObligationRuntimeClient
    from lean_langchain_orchestrator.mcp_server import build_mcp_tools

    client = ObligationRuntimeClient(base_url="http://testserver")
    tools = build_mcp_tools(client)
    expected = {get_mcp_tool_name(op["name"]) for op in OPERATIONS}
    assert set(tools.keys()) == expected


# Catalog operation name -> Python SDK method name (when they differ)
_CATALOG_TO_PY_METHOD = {"check_interactive": "interactive_check"}


def test_python_sdk_has_method_for_each_catalog_operation() -> None:
    """ObligationRuntimeClient has a callable method for every catalog operation."""
    from lean_langchain_sdk.client import ObligationRuntimeClient

    client = ObligationRuntimeClient(base_url="http://test")
    for op in OPERATIONS:
        name = op["name"]
        method_name = _CATALOG_TO_PY_METHOD.get(name, name)
        assert hasattr(client, method_name), f"SDK missing method for catalog operation {name!r}"
        fn = getattr(client, method_name)
        assert callable(fn), f"SDK {method_name!r} is not callable"


def test_gateway_error_envelope_has_code_and_message() -> None:
    """Gateway error responses use stable envelope with code and message (contract for clients)."""
    from fastapi.testclient import TestClient
    from lean_langchain_gateway.api.app import create_app

    app = create_app()
    with TestClient(app) as tc:
        r = tc.get("/v1/reviews/nonexistent-thread")
    assert r.status_code == 404
    body = r.json()
    assert "error" in body
    err = body["error"]
    assert "code" in err
    assert "message" in err
    assert err["code"] == "review_not_found"
