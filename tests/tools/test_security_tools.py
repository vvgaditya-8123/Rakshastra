from tools.registry import discover_builtin_tools, registry

def test_security_tools_registration():
    discover_builtin_tools()
    expected_tools = [
        "security_inventory",
        "security_scan",
        "security_evidence",
        "security_risk",
        "security_report"
    ]
    for tool_name in expected_tools:
        entry = registry.get_entry(tool_name)
        assert entry is not None
        assert entry.toolset == "security"
