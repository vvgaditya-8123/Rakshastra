"""Memory guidance for security-focused cross-session persistence."""

MEMORY_GUIDANCE = (
    "You have persistent memory across sessions. Save durable facts using the memory "
    "tool. Organize memory into the following structural categories:\n"
    "\n"
    "1. **Infrastructure Memory**: Network configurations, firewall rules, routing tables, and topology details.\n"
    "2. **Host Memory**: Operating systems, installed services, kernel configurations, active processes, and users.\n"
    "3. **Threat Memory**: Known vulnerabilities detected, CVE indices, weakness patterns, and scan configurations.\n"
    "4. **Evidence Memory**: Verified logs, signature/checksum records, command output proofs, and audit traces.\n"
    "5. **Compliance Memory**: Regulatory audit findings, policy configurations, and control statuses.\n"
    "6. **Incident Memory**: Historical security incidents, containment actions, and remediation history.\n"
    "7. **Asset Memory**: Device listings, hostnames, inventory endpoints, and software bills of materials (SBOMs).\n"
    "8. **Credential Memory**: API keys metadata, access scopes, and security context placements (do NOT store raw credentials/secrets).\n"
    "\n"
    "Memory is injected into every turn. Keep it compact, structured, and focused on facts that reduce user steering. "
    "Do NOT save temporary task progress, session logs, complete-work timelines, or ephemeral TODOs. "
    "Write memories as declarative facts, not instructions to yourself."
)
