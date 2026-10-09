---
name: weekly-review
description: "The Monday review of a Vitrina workspace in one pass, read-only and cheap: this week vs last for conversations, response times, AI resolution and handoffs, leads won/lost, bookings, CSAT, cost; the ads brief (spend, return, best and wearing ads) when the add-on is on; what the platform flagged (findings, unanswered handoffs, failed jobs, open change requests); and the three things to do this week. Use when the user asks 'cómo nos fue la semana', 'resumen del lunes', 'weekly review', 'qué pasó esta semana', wants a recurring summary for the team or the owner, or asks for the numbers before a meeting."
---

# Weekly review

Summaries only — no thread reading, no edits. Under a minute and under a dollar. Every number comes with its previous-week value; every flag comes with the id to open. Needs `analytics:read, corrections:read, leads:read, followups:read` (+ `ads:read` for the ads block, `worker_failures:read` for failed jobs). Window: `window:"7d"` for insights (the delta is built in), `from`/`to` of the last 7 days for ads.

## Step 1 — Numbers

In one batch: `insights_conversations_get {window:"7d"}` (conversations, first response p50/p90, resolution, billable), `insights_ai_agents_get` (automated, handoffs, deflection, cost), `insights_channels_get` and `insights_sources_get`, `insights_leads_get` (won/lost, win rate, revenue series), `insights_csat_get`, `insights_sla_get` (only if `has_policies`), `followups_overview`, `call_operation insights_resultados_list {from,to}` (bookings, conversation→booking rate, time to book, no-shows). Use `delta_pct` where the block carries it; otherwise compare with a second call on the previous window only for the two or three numbers that matter.

Done when: you have volume, speed, automation, outcome and satisfaction, each with its delta.

## Step 2 — Ads (only with the add-on)

`ads_overview_get {from,to}` (spend, outcomes, return, conversational funnel vs previous), `call_operation ads_briefing_list {screen:"resumen", from, to}` (the platform's own lead sentence and facts), `ads_performance_list {by:"campaign"}` for the best campaign and the one to question, `call_operation ads_creatives_list {window:"7d", limit:10}` for wearing ads, `ads_measurement_list` for open incidents. If `ads_state_list` says the add-on is off, skip the block in one line.

Done when: spend, return, best campaign, wearing ad and measurement state are each one line.

## Step 3 — What the platform flagged

`coach_findings_list {ai_agent_id, status:"active", limit:20}` (new findings this week), `coach_stats` (corrections, proposals pending), `ai_agents_change_requests_list {id, limit:20}` (requests waiting on Vitrina or on you), `worker_failures_list {unreplayed:true, limit:20}`, `insights_overview_live_get` (unattended, unassigned right now). Unanswered handoffs: conversations with `handler:"human"` and no team reply — `call_operation conversations_list {handler:"human", unassigned:true, limit:5}` (rows are ~7k chars each with embeds; five examples are enough, `insights_overview_live_get.unassigned` is the count). `ai_agents_change_requests_list` needs `corrections:read` (app v12.4+; `corrections:write` on older servers); without it, say the requests were not read.

Done when: every open item has an id and an owner (team, agent config, Vitrina).

## Step 4 — Write it

Spanish if the workspace is, under 300 words, in this order: headline (the one number that moved), the table (metric · this week · last week · delta), ads block, flags with ids, **three actions for the week** each naming who does it and which skill or screen (`improve-vitrina-agent`, `analyze-funnel`, `vitrina-ads`, the inbox). State what you could not read (missing scope, add-on off) in one line at the end. Save as `analysis/WEEKLY-<yyyy-mm-dd>.md` if a folder exists; otherwise reply with it.

Done when: an owner can read it in two minutes and knows what to do first.
