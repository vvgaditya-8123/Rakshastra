"""Reporting guidance for security findings and assessment deliverables."""

REPORTING_GUIDANCE = (
    "# Security Operational Reporting\n"
    "\n"
    "When reporting vulnerabilities, risks, or assessment findings, always use a structured framework:\n"
    "- **Likelihood**: How probable is exploitation (Low, Medium, High).\n"
    "- **Impact**: The operational or security consequence if exploited (Low, Medium, High, Critical).\n"
    "- **Exposure**: The reachability/accessibility of the asset.\n"
    "- **Overall Risk Score**: Calculated based on Likelihood and Impact.\n"
    "- **Evidence**: Direct output, logs, or config snippet confirming the issue.\n"
    "- **Remediation**: Actionable remediation steps with least privilege in mind."
)
