---
name: analyze-funnel
description: "Analyze a Vitrina workspace's funnel over MCP/REST: where conversations come from (channels, sources, portals, ads, declared source), how many become leads and move through pipeline stages to won/lost, bookings and attended visits, response and resolution times per channel/source, and where people drop — then say what to change in the agent, the ads or the pipeline. Use when the user asks about embudo, funnel, conversión, tasa de cierre, de dónde vienen los leads/clientes/pacientes, leads por fuente o canal, etapas donde se pierden, cuántas conversaciones terminan en cita/venta, tiempos de respuesta por canal, or wants a weekly/monthly results review — even without the word 'funnel'."
---

# Analyze the funnel

Vitrina records every step as its own object: a **conversation** (with `channel`, `source`, and `ad_origin` when a click-to-WhatsApp ad opened it), a **lead** on a sales pipeline (`source`, `stage`, `status` open|won|lost|unqualified, value), **appointments** (booked, attended), and for clinics the **ads funnel** (contacted → booked → attended → quote → accepted → paid). The platform aggregates each layer; the join between layers is what you compute. Read [`references/funnel-surface.md`](references/funnel-surface.md) before the first call for the tools, their windows and their blind spots. Needs `analytics:read, conversations:read, leads:read, pipelines:read, contacts:read, appointments:read` (+ `ads:read` for ad attribution).

## Step 1 — Frame

Decide the window (insights take `window` 7d|30d|90d|calendar_month|custom with from/to) and the outcome the business counts as success (won lead, booked visit, attended, paid). Name the pipelines in play (`pipelines_list {include:"counts"}` → `stages_list {pipeline_id}`): a workspace often has a sales board and a support board, and the funnel is only the sales one.

Done when: window, success outcome and pipeline ids are fixed. The analysis is read-only; fixes to the board or routing are listed at the end of `references/funnel-surface.md` with the pack each needs.

## Step 2 — Top of funnel: where people come from

`insights_conversations_get` (volume, first-response p50/p90, resolution, billable), `insights_sources_get` and `insights_channels_get` (conversations created in the window by `conversation.source` / channel, with response times), `contacts_stats` (all-time `by_lead_source`, `by_channel`). Ads are invisible in `source`: count them with `conversations_list {from_ad:true, from_date, to_date, limit:100}` (summary rows; page through `page`) or, when the Ads add-on is on, `ads_overview_get` → `conversational.vitrina`. Declared source («¿cómo nos conociste?») lives on contacts as the `declared_source` attribute.

Done when: you have conversations by channel, by source, from ads, with response times per group.

## Step 3 — Middle: leads and stages

`insights_leads_get {window}` for won/lost/unqualified in the window, win rate, cycle time, and `funnel[]` (open count and value per stage — `median_time_in_stage_hours` is always null today). `call_operation leads_summary_list {pipeline_id}` and `leads_funnel_list {pipeline_id}` (all-time, "hours" = since last activity, a proxy not dwell), `leads_win_rate_get {source|owner_user_id|team_id}` for conversion by source/owner. For the leads themselves: `call_operation leads_list {pipeline_id, stage_id?, status, source, sort:"created_desc", fields:"summary", page_size:50}` (no created-date filter; one or two pages, never a whole stage). A lead's stage history is only per lead: `call_operation lead_activity_list {id}` — sample 20–30 won and 20–30 lost leads rather than paging everything.

Done when: for each stage you can say how many are there now, how many won/lost in the window, and the win rate by source.

## Step 4 — Bottom: bookings, visits, payments

`call_operation insights_resultados_list {from,to}` (bookings, AI conversation→booking rate, time to book, no-show recovery, and an `ads` block with cost per booked/attended/paid), `appointments_list {from,to,status[]}` (clinic/test-drive; ≤100 rows per call — count, don't page through thousands), and for clinics `ads_funnel_get` / `call_operation ads_stages_list` for the people cohort with conversion at each step (ad vs other).

Done when: conversations → leads (or bookings) → attended → paid are numbers with the same window.

## Step 5 — Find the leak and its owner

Compute the conversion between adjacent steps and compare to the reference bands (writing → booked 10–15 % healthy for clinics; `ads_stages_list.weakest` names the worst step). For the weakest step, open 5–10 conversations that stalled there (`call_operation conversations_list {source|fromAd, pipelineId, currentStageId}` then `conversations_export`) and classify why: the agent's handling (→ `improve-vitrina-agent`), lead quality by source/ad (→ `vitrina-ads`), human follow-up gaps (unassigned, `awaiting_human_since`, no reply after handoff), or pipeline hygiene (leads parked in a stage for weeks, won leads never closed — the stage audit).

Done when: each leak has a size, an owner and three example conversations.

## Step 6 — Report

`analysis/FUNNEL-<window>.md`: the funnel table (step, count, conversion, vs previous period), by source and by channel, the leaks with evidence, and recommendations split into agent / ads / pipeline / team. State the platform's blind spots in one line when they matter: no cost per lead, no time-in-stage, ads only via `ad_origin`, `insights_leads.open` is a snapshot not a window.

Done when: every recommendation names the layer and the next skill or screen that applies it.
