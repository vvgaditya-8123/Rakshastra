from rakshastra_core.intelligence import AutonomousOrchestrator

def test_goal_planner_and_initialization():
    orchestrator = AutonomousOrchestrator(session_id="SESSION-ORCH-001")
    
    # 1. Initialize case with drug seller context
    orchestrator.initialize_case("MDMA sales on Telegram")
    assert orchestrator.current_objective == "Drug seller"
    assert "Establish target profile on Telegram/WhatsApp" in orchestrator.investigation_plan
    
    # 2. Check generated default tasks
    assert len(orchestrator.tasks) == 3
    task_desc = [t["description"] for t in orchestrator.tasks]
    assert "Search previous investigations for shared identifiers" in task_desc

def test_evidence_queue_reactive_tasks():
    orchestrator = AutonomousOrchestrator(session_id="SESSION-ORCH-002")
    orchestrator.initialize_case("General threat content")

    # Ingest phone number
    orchestrator.ingest_evidence("phone_found", {"phone": "+919893212345"})
    task_desc = [t["description"] for t in orchestrator.tasks]
    assert "Find all aliases for phone: +919893212345" in task_desc

def test_human_approval_gate():
    # Require Approval mode
    orchestrator = AutonomousOrchestrator(session_id="SESSION-ORCH-003", approval_mode="require_approval")
    orchestrator.initialize_case("General threat content")

    # Verify initial tasks are pending and not approved
    for t in orchestrator.tasks:
        assert t["approved"] is False

    # Execute task should fail / return None because none are approved
    executed = orchestrator.execute_next_task()
    assert executed is None

    # Approve one task
    target_id = orchestrator.tasks[0]["id"]
    orchestrator.approve_task(target_id)
    assert orchestrator.tasks[0]["approved"] is True

    # Now executing should run that approved task
    executed = orchestrator.execute_next_task()
    assert executed is not None
    assert executed["id"] == target_id
    assert executed["status"] == "completed"

def test_investigation_memory_cache():
    orchestrator = AutonomousOrchestrator(session_id="SESSION-ORCH-004", approval_mode="auto_execute")
    orchestrator.initialize_case("General threat content")

    # Stash a duplicate task
    task_id = orchestrator.add_task("Decompile bot client if possible", priority=5, usefulness=0.9)
    
    # Run the loop
    res1 = orchestrator.execute_next_task()
    assert res1["description"] == "Decompile bot client if possible"
    assert res1["status"] == "completed"

    # Add it again
    orchestrator.searched_queries.add("Decompile bot client if possible")
    
    # Reset status of the task to pending
    for t in orchestrator.tasks:
        if t["id"] == task_id:
            t["status"] = "pending"

    # Run execution again, it should execute from memory/cache
    res2 = orchestrator.execute_next_task()
    assert res2["status"] == "completed"
    
    state = orchestrator.get_orchestrator_state()
    assert state["memory"]["searched_queries_count"] > 0
