# Agent Evals surface (ADR 0098)

`sk_` key tools. A connector sees only `ai_agents_scenarios_list`, `ai_agents_scenario_runs_list`, `ai_agents_scenario_run_get`, `ai_agents_scenario_suites_list` and `ai_agents_publish_gate_get`; the scenario routes are `interna`, so `call_operation` cannot reach the rest.

| Tool | Scope | Input |
|---|---|---|
| `ai_agents_scenarios_list` | read | `id` (agent), `status?` draft|active|archived, `family?`, `limit?` |
| `ai_agents_scenario_get` | read | `id` (scenario) |
| `ai_agents_scenarios_build` | write | `id`, `from`: description|conversation|bench_session|draft, `description?`, `conversation_id?`, `bench_session_id?`, `draft?`, `note?`, `family?`, `channel?`, `engine?` mock|preview, `agent_version?` — returns a complete draft, **not saved** |
| `ai_agents_scenario_create` | write | `id` + body `{name, family?, tags?, channel?, persona:{name?, register?, script:[{role: customer|agent, text}]}, world?:{engine: mock|preview, clock?, …seeded state}, checks:[…], hard_fails:[…]}` |
| `ai_agents_scenario_update` | write | `id`, `scenario_id`, `patch` (same shape; persona/world/checks/channel changes bump the version) |
| `ai_agents_scenario_delete`, `ai_agents_scenarios_import` (≤200 bodies) | write | |
| `ai_agents_scenarios_run` | simulate | `id`, `scenario_ids?` (absent = every ACTIVE scenario), `agent_version` draft|live, `repeats?` → `batch_id`, returns immediately |
| `ai_agents_scenario_runs_list` | read | `id`, `scenario_id?`, `batch_id?`, `status?`, `limit?` — status, score, hard-fail/check counts, timings, `draft_fingerprint` |
| `ai_agents_scenario_run_get` | read | `id` (run) — transcript with tool calls, sandbox final state, every check with evidence, hard fails, score |
| `ai_agents_scenario_runs_cancel` | simulate | `id`, `batch_id?` or `scenario_ids?` |
| `ai_agents_scenario_repair` | write | `id`, `scenario_id`, `run_id`, `note?` — the scenario builder rewrites the scenario from the run |
| `ai_agents_scenario_suites_list` | read | `id`, `kind?`, `enabled?`, `limit?` |
| `ai_agents_scenario_suite_create` | write | `id` + `{name, kind: golden|nightly|exploratory|on_change, filter?:{families?, tags?, scenario_ids?}, policy?:{block_publish_on_hard_fail?, min_pass_rate?, …}, cron?}` |
| `ai_agents_scenario_suite_update` / `_delete` | write | `suite_id`, `patch` |
| `ai_agents_scenario_suite_run` | simulate | `id`, `suite_id`, `agent_version?`, `repeats?` → suite run |
| `ai_agents_scenario_suite_runs_list` | read | `id`, `suite_id?`, `status?`, `trigger?` — each with `summary {n, passed, partial, failed, error, hard_fails, pass_rate, flaky, cost_usd, duration_ms}` and `delta` vs previous |
| `ai_agents_scenario_suite_run_get` | read | `id` (suite run) — plus one summary per scenario run |
| `ai_agents_publish_gate_get` | read | `id` (agent) — `none|ready|blocked|stale|pending` from the enabled golden suite |
| `ai_agent_simulate` | simulate | `ai_agent_id`, `user_message`, `use_draft?`, `channel?` — one turn, tools declared not executed |

REST twins live under `/ai-agents/{id}/scenarios…`, `/scenario-suites…`, `/scenario-runs…`, `/publish-gate` (beta). Runs execute on the platform's evals pool; `queued` for more than ~10 minutes means the pool is down — that is Vitrina's, report it. Test-bench sessions (`/ai-agents/{id}/test-sessions`, ADR 0090) are the interactive cousin: a saved chat with comments you can send to the Coach or turn into a scenario (`from:"bench_session"`).

Verdicts: `passed`, `partial` (checks failed, no hard fail), `failed` (hard fail), `error` (platform/tool error), `cancelled`. `draft_fingerprint` on a run says which draft it exercised; a run older than the current draft is stale evidence.
