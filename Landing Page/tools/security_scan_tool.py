import socket
import os
import subprocess
from datetime import datetime
from pathlib import Path
from rakshastra_constants import get_rakshastra_home
from rakshastra_core.models import Scan, Evidence, Severity, Confidence
from rakshastra_core.engines import EvidenceStore
from tools.registry import registry, tool_result, tool_error

import uuid
from rakshastra_core.engines.workflow import SecurityWorkflowEngine
from rakshastra_core.models.workflow import WorkflowStep

def check_security_requirements() -> bool:
    return True

def _get_evidence_store() -> EvidenceStore:
    db_path = get_rakshastra_home() / "security.db"
    return EvidenceStore(db_path)

def _handle_security_scan(args: dict, **kwargs) -> str:
    session_id = kwargs.get("session_id") or os.environ.get("RAKSHASTRA_SESSION_ID", "default_session")
    db_path = get_rakshastra_home() / "security.db"
    wf_engine = SecurityWorkflowEngine(db_path)
    current_wf_phase = wf_engine.get_active_phase(session_id)
    scan_type = args.get("scan_type", "network").lower()
    target = args.get("target", "127.0.0.1")

    res = _handle_security_scan_inner(args, **kwargs)

    status = "completed" if "error" not in str(res) else "failed"
    step = WorkflowStep(
        id=str(uuid.uuid4()),
        created_at=datetime.utcnow().isoformat() + "Z",
        session_id=session_id,
        phase=current_wf_phase,
        command=f"security_scan(scan_type={scan_type}, target={target})",
        status=status,
        duration=0.0,
        output_summary=f"Executed security scan: {scan_type} on {target}."
    )
    wf_engine.log_step(step)
    return res

def _handle_security_scan_inner(args: dict, **kwargs) -> str:
    scan_type = args.get("scan_type", "network").lower()
    target = args.get("target", "127.0.0.1")
    options = args.get("options", {})

    store = _get_evidence_store()
    scan = Scan(
        scan_type=scan_type,
        target=target,
        status="running",
        started_at=datetime.utcnow().isoformat() + "Z"
    )

    findings_count = 0
    evidence_ids = []

    try:
        if scan_type == "network":
            ports = options.get("ports", [22, 80, 443, 8080, 3306, 5432, 27017])
            timeout = options.get("timeout", 0.5)
            
            for port in ports:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(timeout)
                result = s.connect_ex((target, port))
                s.close()
                if result == 0:
                    ev = Evidence(
                        tool="security_scan",
                        host=target,
                        timestamp=datetime.utcnow().isoformat() + "Z",
                        finding=f"Port {port} is open on target host.",
                        raw_output=f"Port {port}/tcp is OPEN",
                        severity=Severity.MEDIUM if port in [22, 3306, 5432] else Severity.LOW,
                        confidence=Confidence.CONFIRMED,
                        tags=["network", "port", "exposed"],
                        context={"port": port, "protocol": "tcp"}
                    )
                    store.record(ev)
                    evidence_ids.append(ev.id)
                    findings_count += 1

        elif scan_type == "credentials":
            workspace = target if target != "127.0.0.1" else os.getcwd()
            scan_path = Path(workspace)
            patterns = ["*.env", "config.json", "credentials.json"]
            found_files = []
            for pat in patterns:
                found_files.extend(list(scan_path.glob(f"**/{pat}")))
            
            keywords = ["api_key", "secret", "password", "token", "private_key"]
            for file_path in found_files:
                if "node_modules" in str(file_path) or ".git" in str(file_path):
                    continue
                try:
                    content = file_path.read_text(encoding="utf-8", errors="ignore")
                    for line_num, line in enumerate(content.splitlines(), 1):
                        if any(kw in line.lower() and "=" in line for kw in keywords):
                            parts = line.split("=", 1)
                            key_part = parts[0].strip()
                            ev = Evidence(
                                tool="security_scan",
                                host="localhost",
                                timestamp=datetime.utcnow().isoformat() + "Z",
                                finding=f"Potential credential exposure in file {file_path.name}:{line_num}.",
                                raw_output=f"{file_path.name}:{line_num}: {key_part}= [REDACTED]",
                                severity=Severity.HIGH,
                                confidence=Confidence.HIGH,
                                tags=["credential", "secret", "file-leak"],
                                context={"file": str(file_path), "line": line_num, "key": key_part}
                            )
                            store.record(ev)
                            evidence_ids.append(ev.id)
                            findings_count += 1
                except Exception:
                    pass

        elif scan_type == "docker":
            socket_path = "/var/run/docker.sock"
            pipe_path = "//./pipe/docker_engine"
            socket_exists = os.path.exists(socket_path) or os.path.exists(pipe_path)
            
            if socket_exists:
                ev = Evidence(
                    tool="security_scan",
                    host="localhost",
                    timestamp=datetime.utcnow().isoformat() + "Z",
                    finding="Docker socket is accessible locally.",
                    raw_output=f"Docker socket found: {socket_path if os.path.exists(socket_path) else pipe_path}",
                    severity=Severity.LOW,
                    confidence=Confidence.CONFIRMED,
                    tags=["docker", "socket", "local-access"],
                    context={"socket_path": socket_path if os.path.exists(socket_path) else pipe_path}
                )
                store.record(ev)
                evidence_ids.append(ev.id)
                findings_count += 1

        elif scan_type == "linux" or scan_type == "windows":
            if os.name == "nt" and scan_type == "windows":
                try:
                    res = subprocess.run(["netsh", "advfirewall", "show", "allprofiles"], 
                                         capture_output=True, text=True, timeout=5)
                    if "State" in res.stdout:
                        ev = Evidence(
                            tool="security_scan",
                            host="localhost",
                            timestamp=datetime.utcnow().isoformat() + "Z",
                            finding="Windows Firewall profiles retrieved.",
                            raw_output=res.stdout[:500],
                            severity=Severity.INFO,
                            confidence=Confidence.CONFIRMED,
                            tags=["windows", "firewall", "audit"],
                            context={"firewall_output": res.stdout[:200]}
                        )
                        store.record(ev)
                        evidence_ids.append(ev.id)
                        findings_count += 1
                except Exception:
                    pass
            elif os.name != "nt" and scan_type == "linux":
                shadow_path = Path("/etc/shadow")
                if shadow_path.exists():
                    stat = shadow_path.stat()
                    is_world_readable = (stat.st_mode & 0o004) != 0
                    if is_world_readable:
                        ev = Evidence(
                            tool="security_scan",
                            host="localhost",
                            timestamp=datetime.utcnow().isoformat() + "Z",
                            finding="/etc/shadow is world-readable! Critical security risk.",
                            raw_output=f"Permissions: {oct(stat.st_mode)}",
                            severity=Severity.CRITICAL,
                            confidence=Confidence.CONFIRMED,
                            tags=["linux", "permissions", "shadow-file"],
                            context={"mode": oct(stat.st_mode)}
                        )
                        store.record(ev)
                        evidence_ids.append(ev.id)
                        findings_count += 1

        scan.status = "completed"
        scan.completed_at = datetime.utcnow().isoformat() + "Z"
        scan.evidence_ids = evidence_ids
        scan.summary = {"findings_count": findings_count}

        return tool_result(
            success=True,
            scan_type=scan_type,
            target=target,
            status=scan.status,
            findings_count=findings_count,
            evidence_ids=evidence_ids
        )

    except Exception as e:
        scan.status = "failed"
        scan.completed_at = datetime.utcnow().isoformat() + "Z"
        return tool_error(f"Security scan failed: {str(e)}")

SECURITY_SCAN_SCHEMA = {
    "name": "security_scan",
    "description": "Orchestrates and executes non-destructive security scanning for host discovery, port scanning, or credentials scanning.",
    "parameters": {
        "type": "object",
        "properties": {
            "scan_type": {
                "type": "string",
                "enum": ["network", "docker", "linux", "windows", "credentials"],
                "description": "The type of security scan to execute."
            },
            "target": {
                "type": "string",
                "default": "127.0.0.1",
                "description": "Target IP, hostname, subnet, container ID, or workspace folder."
            },
            "options": {
                "type": "object",
                "description": "Optional parameters, e.g. ports (array of integers) or custom scan timeout."
            }
        },
        "required": ["scan_type"]
    }
}

registry.register(
    name="security_scan",
    toolset="security",
    schema=SECURITY_SCAN_SCHEMA,
    handler=_handle_security_scan,
    check_fn=check_security_requirements,
    emoji="🔍"
)
