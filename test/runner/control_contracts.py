"""Adapt only absent control-RPC errors to the isolated empty-Commands gateway.

The upstream contract remains unchanged on disk. Raw telemetry and every
business log still go through the original Collector and A/B comparison.
"""
from copy import deepcopy

CONTROL_METHODS = (
    "skywalking.v3.ConfigurationDiscoveryService/fetchConfigurations",
    "skywalking.v3.ProfileTask/getProfileTaskCommands",
    "skywalking.v10.PprofTask/getPprofTaskCommands",
)


def gateway_contract(original):
    result = deepcopy(original)
    removed = 0
    for group in result.get("logItems", []):
        kept = []
        for entry in group.get("logs", []):
            text = entry.get("body", {}).get("content", {}).get("text", "")
            context = entry.get("traceContext", {})
            absent_control_error = (
                entry.get("endpoint") == ""
                and context.get("traceId") == "N/A"
                and context.get("traceSegmentId") == "N/A"
                and context.get("spanId") == -1
                and "code = Unimplemented" in text
                and any(f"Method not found: {method}" in text for method in CONTROL_METHODS)
            )
            if absent_control_error:
                removed += 1
            else:
                kept.append(entry)
        group["logs"] = kept
        if kept:
            group["logSize"] = f"ge {len(kept)}"
    return result, removed
