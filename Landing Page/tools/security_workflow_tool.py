import os
import uuid
from datetime import datetime
from pathlib import Path

from rakshastra_constants import get_rakshastra_home
from rakshastra_core.models.workflow import WorkflowState, WorkflowStep
from rakshastra_core.engines import SecurityWorkflowEngine, SecurityReasoningEngine
from tools.registry import registry, tool_result, tool_error

def check_security_requirements() -> bool:
    return True

def _get_workflow_engine() -> SecurityWorkflowEngine:
    db_path = get_rakshastra_home() / "security.db"
    return SecurityWorkflowEngine(db_path)

def _get_reasoning_engine() -> SecurityReasoningEngine:
    return SecurityReasoningEngine()

def _handle_security_workflow(args: dict, **kwargs) -> str:
    action = args.get("action")
    # TUI and CLI pass session_id in kwargs or env RAKSHASTRA_TUI_RESUME / session context
    session_id = kwargs.get("session_id") or os.environ.get("RAKSHASTRA_SESSION_ID", "default_session")

    engine = _get_workflow_engine()
    reasoning = _get_reasoning_engine()

    try:
        if action == "get_state":
            phase = engine.get_active_phase(session_id)
            guidance = reasoning.get_guidance(session_id, engine)
            return tool_result(
                success=True,
                session_id=session_id,
                current_phase=phase.value,
                guidance=guidance
            )

        elif action == "transition_state":
            phase_str = args.get("phase")
            if not phase_str:
                return tool_error("Phase argument is required for transition_state.")
            
            try:
                target_phase = WorkflowState(phase_str)
            except ValueError:
                valid_phases = [p.value for p in SecurityWorkflowEngine.PHASE_SEQUENCE]
                return tool_error(f"Invalid phase: '{phase_str}'. Valid phases are: {valid_phases}")

            success = engine.transition_to(session_id, target_phase)
            if not success:
                active_phase = engine.get_active_phase(session_id)
                return tool_error(
                    f"Transition failed. Enforcing deterministic sequence. "
                    f"You cannot transition to '{phase_str}' from '{active_phase.value}' directly."
                )

            # Retrieve updated guidance
            guidance = reasoning.get_guidance(session_id, engine)
            return tool_result(
                success=True,
                session_id=session_id,
                transitioned_to=target_phase.value,
                guidance=guidance
            )

        elif action == "log_step":
            phase_str = args.get("phase")
            command = args.get("command", "")
            status = args.get("status", "completed")
            duration = args.get("duration", 0.0)
            output_summary = args.get("output_summary", "")

            if not phase_str:
                phase_str = engine.get_active_phase(session_id).value

            try:
                phase = WorkflowState(phase_str)
            except ValueError:
                return tool_error(f"Invalid phase: '{phase_str}'")

            step = WorkflowStep(
                id=str(uuid.uuid4()),
                created_at=datetime.utcnow().isoformat() + "Z",
                session_id=session_id,
                phase=phase,
                command=command,
                status=status,
                duration=duration,
                output_summary=output_summary
            )
            step_id = engine.log_step(step)
            return tool_result(
                success=True,
                session_id=session_id,
                logged_step_id=step_id,
                phase=phase_str
            )

        elif action == "get_history":
            history = engine.get_history(session_id)
            history_list = []
            for step in history:
                history_list.append({
                    "id": step.id,
                    "created_at": step.created_at,
                    "phase": step.phase.value,
                    "command": step.command,
                    "status": step.status,
                    "duration": step.duration,
                    "output_summary": step.output_summary
                })
            return tool_result(
                success=True,
                session_id=session_id,
                history=history_list
            )

        else:
            return tool_error(f"Unknown action: {action}")

    except Exception as e:
        return tool_error(f"Workflow operation failed: {str(e)}")

SECURITY_WORKFLOW_SCHEMA = {
    "name": "security_workflow",
    "description": "Enforces and tracks the deterministic 9-phase security investigation workflow (Recon -> Enumeration -> Collection -> Evidence -> Analysis -> Prioritization -> Recommendation -> Verification -> Report).",
    "parameters": {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": ["get_state", "transition_state", "log_step", "get_history"],
                "description": "The workflow engine action to execute."
            },
            "phase": {
                "type": "string",
                "description": "Workflow phase to transition to or log a step under. E.g., 'Recon', 'Enumeration', 'Collection', 'Evidence', 'Analysis', 'Prioritization', 'Recommendation', 'Verification', 'Report'."
            },
            "command": {
                "type": "string",
                "description": "The command executed (for log_step)."
            },
            "status": {
                "type": "string",
                "enum": ["completed", "failed", "skipped"],
                "description": "Status of the logged step."
            },
            "duration": {
                "type": "number",
                "description": "Execution duration in seconds (for log_step)."
            },
            "output_summary": {
                "type": "string",
                "description": "Brief summary of output findings (for log_step)."
            }
        },
        "required": ["action"]
    }
}

registry.register(
    name="security_workflow",
    toolset="security",
    schema=SECURITY_WORKFLOW_SCHEMA,
    handler=_handle_security_workflow,
    check_fn=check_security_requirements,
    emoji="⚙"
)
