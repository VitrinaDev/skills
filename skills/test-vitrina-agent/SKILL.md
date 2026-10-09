---
name: test-vitrina-agent
description: "Test a Vitrina AI agent with scenarios (Agent Evals): turn a real conversation or a described situation into a scenario (persona script, mock world, checks), run it against the draft or the live agent, read the transcript and check results, group scenarios into suites — golden (gates publishing), nightly, exploratory — and keep a fixed bug from coming back. Use when the user asks to test the agent, 'que no vuelva a pasar', 'prueba que…', 'crea un escenario/eval', wants to run the suite before publishing, asks why the publish gate is blocked, or wants to see how a scenario run went."
---

# Test the agent with scenarios

A **scenario** is a customer persona with a script, a seeded mock world (agenda, catalogue, clock) and checks (hard fails + scored checks); a **run** executes the agent against it and records transcript, tool calls, check evidence and a judge score. A **suite** is a named set with a policy; the **golden** suite gates `POST /publish` (REST; the MCP `ai_agents_publish` skips the gate). Runs are queued and take ~1–3 minutes each. Scopes: `ai_agents:read/write/simulate`. Tool inputs are in [`references/evals-surface.md`](references/evals-surface.md).

## Step 1 — Start from evidence

The best scenario is a conversation that went wrong: `ai_agents_scenarios_build {id, from:"conversation", conversation_id, note:"<what should have happened>"}` writes a complete draft (persona, world, checks) from it without saving. From a description: `from:"description", description:"…"`. Read the draft critically: the persona script must reproduce the trigger, the world must contain what the tools need (a free slot, the service, the patient), and the checks must assert the **behaviour the user wants**, not the old output.

Done when: the draft's hard fails and checks state the expected behaviour in one sentence each.

## Step 2 — Save and run

`ai_agents_scenario_create {id, ...draft}` then `ai_agents_scenarios_run {id, scenario_ids:[…], agent_version:"draft"|"live", repeats:1}`; poll `ai_agents_scenario_runs_list {id, batch_id}` until every run has a status; `ai_agents_scenario_run_get {id, run_id}` for the transcript, tool calls, check evidence and hard fails (summary by default since app v12.4; `detail:"full"` adds reasoning and the sandbox state, 80–230k chars — only when a check's evidence is not enough). Runs take 2–6 minutes: wait with a single `sleep 120` then poll `ai_agents_scenario_runs_list {id, batch_id}`. Test the **draft** when a fix is pending, the **live** version when auditing.

Done when: each run has a verdict and you have read the transcript of every failed or partial one.

## Step 3 — Read a failure honestly

A red run has three possible causes: the agent (the fix belongs in `improve-vitrina-agent`), the scenario (persona script or world wrong, a check asserting the wrong thing — `ai_agents_scenario_repair {id, scenario_id, run_id, note}` rewrites it from the run), or the platform (a tool error inside the mock world, `status: error`). Say which, with the evidence line from the transcript. Flaky runs (`repeats:3`, mixed verdicts) are a prompt or model problem, not a test problem.

Done when: every red run is attributed to agent, scenario or platform.

## Step 4 — Keep it

Put regression scenarios in the **golden** suite (`ai_agents_scenario_suite_create {id, name, kind:"golden", filter:{tags|scenario_ids}, policy:{block_publish_on_hard_fail:true, min_pass_rate}}`; one suite per agent, add scenarios by tag). `ai_agents_scenario_suite_run` after every fix; `ai_agents_publish_gate_get {id}` tells whether publishing is allowed (`blocked`/`stale` block, `pending` warns, `none` never blocks). Nightly suites notify; exploratory ones never block.

Done when: the scenario is active, tagged into the golden suite, and the last suite run is green or its red is explained. A scenario that passed on every repeat without ever having failed has not yet proved it catches the bug: say so, and run it against the version that produced the original conversation (`versions_list`, `agent_version:"draft"` after `versions_restore`) when that version still exists.

## Step 5 — Report

Scenario ids and names, versions tested, verdicts with one line of evidence each, what changed in the agent (if anything), and the gate state. A scenario that always passes regardless of the agent proves nothing — say so and tighten the check.
