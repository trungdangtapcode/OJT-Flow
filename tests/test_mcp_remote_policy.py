from pathlib import Path

from ojtflow.infrastructure.mcp_catalogs import load_mcp_remote_deployment_policy


ROOT = Path(__file__).resolve().parents[1]


def test_remote_mcp_policy_blocks_remote_until_required_controls_exist() -> None:
    policy = load_mcp_remote_deployment_policy(ROOT / "knowledge")

    assert policy.version == "remote_mcp_deployment_policy.v1"
    assert policy.remote_exposure_allowed is False
    assert policy.status == "design_only"
    control_ids = {control.control_id for control in policy.required_controls}
    assert {
        "oauth_protected_resource_metadata",
        "resource_indicators",
        "per_user_tool_scoping",
        "remote_rate_limits",
        "audit_correlation",
        "tool_manifest_review",
    } <= control_ids
    assert all(control.blocks_remote for control in policy.required_controls)
    assert policy.oauth["protected_resource_metadata_required"] is True
    assert policy.resource_indicators["required"] is True
    assert policy.audit["raw_payload_storage"] == "forbidden"
