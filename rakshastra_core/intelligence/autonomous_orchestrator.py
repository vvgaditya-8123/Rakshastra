import uuid
from typing import Dict, Any, List, Optional, Set

class AutonomousOrchestrator:
    """Orchestrates autonomous cyber investigations by planning goals, executing tasks, and maintaining memory."""

    VALID_OBJECTIVES = {"Drug seller", "Drug buyer", "Money mule", "Bot operator", "Scam network", "Unknown actor"}
    APPROVAL_MODES = {"auto_execute", "suggest_only", "require_approval"}

    def __init__(
        self,
        session_id: str,
        approval_mode: str = "auto_execute",
        confidence_threshold: float = 0.85
    ):
        if approval_mode not in self.APPROVAL_MODES:
            raise ValueError(f"Invalid Approval Mode: {approval_mode}")
            
        self.session_id = session_id
        self.approval_mode = approval_mode
        self.confidence_threshold = confidence_threshold

        # Case Goals & State
        self.current_objective: str = "Unknown actor"
        self.investigation_plan: List[str] = []
        self.completion_percentage: float = 0.0

        # Tasks & Queue
        self.tasks: List[Dict[str, Any]] = [] # Task Tree
        self.evidence_queue: List[Dict[str, Any]] = []
        
        # Memory & Logs
        self.searched_queries: Set[str] = set()
        self.failed_queries: Set[str] = set()
        self.succeeded_queries: Set[str] = set()
        self.decision_log: List[Dict[str, Any]] = [] # Decision Tree
        
        # Current Metrics
        self.current_confidence: float = 0.0
        self.remaining_unknowns: List[str] = ["Operator identity", "Full footprint map"]

    def log_decision(self, action: str, reason: str):
        """Append an entry to the AI Decision Log."""
        import datetime
        self.decision_log.append({
            "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
            "action": action,
            "reason": reason
        })

    # ── Case Goal Planner ────────────────────────────────────────────────────

    def initialize_case(self, threat_text: str):
        """Analyze threat context to define investigation objective and plan."""
        text_lower = threat_text.lower()
        
        if any(w in text_lower for w in ["mdma", "molly", "weed", "ganja", "coke", "drugs"]):
            self.current_objective = "Drug seller"
            self.investigation_plan = [
                "Establish target profile on Telegram/WhatsApp",
                "Extract drug dealer cryptocurrency wallet",
                "Map contact phone numbers and aliases",
                "Trace financial cashout trails"
            ]
        elif any(w in text_lower for w in ["mule", "cashout", "bank drop", "receiving agent"]):
            self.current_objective = "Money mule"
            self.investigation_plan = [
                "Scan bank drop details",
                "Link money routing networks",
                "Identify recruiter recruitment channels"
            ]
        elif any(w in text_lower for w in ["giveaway", "lottery", "presale", "airdrop"]):
            self.current_objective = "Scam network"
            self.investigation_plan = [
                "Deconstruct phishing dApp/domain hosting",
                "Trace fraudulent transaction addresses",
                "Map social handles advertising scam"
            ]
        elif any(w in text_lower for w in ["bot online", "automation", "/start", "/buy"]):
            self.current_objective = "Bot operator"
            self.investigation_plan = [
                "Analyze API endpoint command structure",
                "Decompile bot client if possible",
                "Flag bot servers"
            ]
        else:
            self.current_objective = "Unknown actor"
            self.investigation_plan = [
                "Extract initial text footprints",
                "Check for basic alias linkages"
            ]

        self.log_decision(
            action=f"Set Objective to {self.current_objective}",
            reason=f"Threat context text matching keywords resulted in planning: {self.investigation_plan}."
        )
        
        # Populate initial default tasks
        self._generate_initial_tasks()

    # ── Dynamic Task Planning & Evidence Queue ───────────────────────────────

    def _generate_initial_tasks(self):
        """Spawn baseline investigative tasks based on current objective."""
        self.add_task(
            description="Extract OCR footprints from attached screenshots",
            priority=3,
            usefulness=0.80
        )
        self.add_task(
            description="Perform reverse username lookup on social handles",
            priority=4,
            usefulness=0.85
        )
        self.add_task(
            description="Search previous investigations for shared identifiers",
            priority=4,
            usefulness=0.90
        )

    def add_task(
        self,
        description: str,
        priority: int,
        usefulness: float,
        dependencies: Optional[List[str]] = None
    ) -> str:
        """Create and queue a dynamic task."""
        # Avoid duplicate task creation
        if any(t["description"] == description for t in self.tasks):
            return ""

        task_id = f"TASK-{str(uuid.uuid4())[:8].upper()}"
        self.tasks.append({
            "id": task_id,
            "description": description,
            "priority": priority,
            "status": "pending",
            "estimated_usefulness": usefulness,
            "dependencies": dependencies or [],
            "approved": True if self.approval_mode == "auto_execute" else False
        })
        self.log_decision(
            action=f"Created task {task_id}",
            reason=f"Dynamic request generated: '{description}' (priority={priority}, usefulness={usefulness})."
        )
        return task_id

    def approve_task(self, task_id: str) -> bool:
        """Manually approve a task for execution."""
        for t in self.tasks:
            if t["id"] == task_id:
                t["approved"] = True
                self.log_decision(action=f"Approved task {task_id}", reason="Investigator issued manual approval.")
                return True
        return False

    def ingest_evidence(self, event_type: str, data: Dict[str, Any]):
        """Reactive task creation based on incoming evidence queues."""
        self.evidence_queue.append({"event_type": event_type, "data": data})
        
        # Reactive rules
        if event_type == "invite_link_found":
            invite = data.get("invite_link")
            if invite:
                self.add_task(
                    description=f"Search every investigation for same invite link: {invite}",
                    priority=4,
                    usefulness=0.75
                )
        elif event_type == "wallet_found":
            wallet = data.get("wallet")
            if wallet:
                self.add_task(
                    description=f"Expand graph around wallet: {wallet}",
                    priority=5,
                    usefulness=0.95
                )
        elif event_type == "phone_found":
            phone = data.get("phone")
            if phone:
                self.add_task(
                    description=f"Find all aliases for phone: {phone}",
                    priority=5,
                    usefulness=0.90
                )
        elif event_type == "username_found":
            username = data.get("username")
            if username:
                self.add_task(
                    description=f"Analyze profile for handle: {username}",
                    priority=4,
                    usefulness=0.85
                )

    # ── Autonomous Investigation Loop ────────────────────────────────────────

    def execute_next_task(self) -> Optional[Dict[str, Any]]:
        """Executes the highest-priority pending and approved task."""
        # Find candidate tasks: approved, pending, and dependencies met
        candidates = []
        completed_ids = {t["id"] for t in self.tasks if t["status"] == "completed"}
        
        for t in self.tasks:
            if t["status"] == "pending" and t["approved"]:
                # Check dependencies
                deps_met = all(dep in completed_ids for dep in t["dependencies"])
                if deps_met:
                    candidates.append(t)

        if not candidates:
            return None

        # Sort by priority desc, usefulness desc
        candidates.sort(key=lambda x: (x["priority"], x["estimated_usefulness"]), reverse=True)
        target_task = candidates[0]

        target_task["status"] = "in_progress"
        self.log_decision(
            action=f"Started execution of {target_task['id']}",
            reason=f"Selected highest priority candidate: '{target_task['description']}'."
        )

        # Simulate execution processing (modulating success vs failure / memory cache)
        desc = target_task["description"]
        if desc in self.searched_queries:
            # Avoid duplicate work
            target_task["status"] = "completed"
            self.log_decision(
                action=f"Completed {target_task['id']} (cached)",
                reason="Task query was already stored in memory; skipped duplicate execution."
            )
            return target_task

        self.searched_queries.add(desc)
        
        # Basic mock execution results
        success = True
        if "failed" in desc.lower() or random_prob() < 0.1: # 10% simulated failure rate
            success = False

        if success:
            target_task["status"] = "completed"
            self.succeeded_queries.add(desc)
            self.log_decision(
                action=f"Completed {target_task['id']} (success)",
                reason=f"Successfully executed task query: '{desc}'."
            )
            # Increase confidence
            self.current_confidence = min(self.current_confidence + 0.15, 1.0)
        else:
            target_task["status"] = "failed"
            self.failed_queries.add(desc)
            self.log_decision(
                action=f"Failed {target_task['id']}",
                reason=f"Execution failed for task query: '{desc}'."
            )

        # Update progress metric
        completed_count = len([t for t in self.tasks if t["status"] in {"completed", "failed"}])
        self.completion_percentage = round((completed_count / len(self.tasks)) * 100, 1)

        # Check confidence-driven rules
        if self.current_confidence >= self.confidence_threshold:
            self.remaining_unknowns = []
            self.log_decision(
                action="Raised Alert Recommendations",
                reason=f"Confidence threshold reached ({self.current_confidence} >= {self.confidence_threshold}). Recommending direct investigator intervention."
            )

        return target_task

    # ── Output State ─────────────────────────────────────────────────────────

    def get_orchestrator_state(self) -> Dict[str, Any]:
        """Return the current investigation orchestrator state in structured JSON."""
        return {
            "session_id": self.session_id,
            "current_objective": self.current_objective,
            "investigation_plan": self.investigation_plan,
            "current_confidence": round(self.current_confidence, 3),
            "completion_percentage": self.completion_percentage,
            "remaining_unknowns": self.remaining_unknowns,
            "task_tree": self.tasks,
            "decision_tree": self.decision_log,
            "memory": {
                "searched_queries_count": len(self.searched_queries),
                "succeeded_queries_count": len(self.succeeded_queries),
                "failed_queries_count": len(self.failed_queries)
            }
        }


def random_prob() -> float:
    # Deterministic wrapper for random probability in tests
    import random
    return random.random()
