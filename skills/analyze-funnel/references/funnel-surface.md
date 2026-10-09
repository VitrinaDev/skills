# Funnel surface — tools, windows, blind spots

## Vocabularies

- `conversation.source` = `lead.source` ∈ conversation, marketplace, manual, import, ai_agent, chileautos, yapo, mercadolibre, website, facebook_marketplace, form (null shows as `__none__`). Portals: mercadolibre, yapo, chileautos. `contact.origin_channel` uses the same list. **Ads are never a source**: use `ad_origin` / `fromAd`.
- `lead.status` open|won|lost|unqualified; `lead.intent` buy|sell|financing|trade_in. Display ids `L-n`, conversations `C-n`.
- Conversation `handler` bot|human|external; `awaiting_human_since` marks a pending handoff.

## Insights (MCP, `analytics:read`)

Window args: `window` required (24h|7d|30d|90d|calendar_month|calendar_year|custom), optional `month` YYYY-MM, `year`, `from`/`to` (custom: ISO instants, `to` exclusive). Response `{data, meta.window}`.

| Tool | Output |
|---|---|
| `insights_conversations_get` | blocks `conversations`, `messages_in/out`, `first_response_seconds`, `resolution_seconds`, `resolutions`, `customer_wait_seconds` (each `total/avg`, `delta_pct`, `series[]`); `first_response_p50/p90_seconds`, `facturables`, `solo_humano` |
| `insights_sources_get` / `insights_channels_get` / `insights_tags_get` / `insights_teams_get` | rows `{key, label, conversations, avg_first_response_seconds, avg_resolution_seconds, avg_customer_wait_seconds, resolutions}` — conversations **created** in the window; absent key = 0 |
| `insights_agents_get` | per human: replies, avg response, breakdown fields |
| `insights_ai_agents_get` / `insights_bots_get` | automated conversations, handoffs, deflection/handoff rate, cost, latency |
| `insights_leads_get` | `open` (snapshot, not windowed), `won/lost/unqualified` (closed in window), values (+by currency), `win_rate` = won/(won+lost), `avg_cycle_seconds`, `created_series`, `won_series`, `revenue_series`, `funnel[]{stage_id, stage_name, position, open_count, total_value, median_time_in_stage_hours: null}` across every sales pipeline. **No source breakdown.** |
| `insights_csat_get` | AI-estimated satisfaction, `recent` ≤50 |
| `insights_sla_get` | targets, hit rate, breaches ≤50 |
| `insights_storefront_get {month?}` | storefront visits, leads, conversion, top vehicles |
| `insights_overview_live_get`, `insights_overview_heatmap_get {tz}` | live counters; traffic/resolutions by day×hour |
| `call_operation insights_resultados_list {from,to}` | bookings, `ai.conversation_rate` (conversation→booking), autonomy, `time_to_book`, no-show recovery, `ads{spend_clp, booked, attended, paid, cost_per_booked, cost_per_attended, cost_per_paid}`; clinic twins `clinic_insights_resultados_list`, `clinic_insights_comercial_list` |

## Leads and pipelines

- `pipelines_list {include:"counts"}` (`card_count`), `stages_list {pipeline_id}` (`pipelines:read`).
- `leads_kanban {pipeline_id?}` — without id: boards and stages; with id: the whole board (≤200 leads per stage, large). `lead_conversations_list {lead_id}`, `lead_interests_list {lead_id}`.
- `call_operation leads_list` filters: `pipeline_id, stage_id, status, source, intent, owner_user_id, team_id, contact_id, min/max_value, temperature, last_activity_after` (the only date filter), `q`, `sort` (`created_desc`, `source_asc`, `stage_asc`), `page`, `page_size≤200`.
- All-time analytics (`pipeline_id` only): `leads_summary_list`, `leads_stats_list` (score bands), `leads_funnel_list` (open count, value, median "hours" = now − last activity), `leads_win_rate_get {owner_user_id|team_id|source}`.
- Per lead: `lead_activity_list {id}` — kinds created, stage_changed, won, lost (the only stage history read; the `stage_transition_log` table has no endpoint).
- Links: `lead.origin_conversation_id`, `lead_conversation` (`is_primary`); reverse: `conversations_linked_records {id}`.

## Conversations and contacts

- MCP `conversations_list {page, limit≤100, channel, status, search}` — **no** source/date/ad filters. REST via `call_operation conversations_list {source, fromAd, aiReplied, fromDate, toDate, pipelineId, currentStageId, handler, unassigned, sort, page, limit}` has them; rows carry `ad_origin`.
- `conversations_export {id, format:"json"}` for one thread; `conversations_linked_records {id}`.
- `contacts_stats {}` (all-time: total, by_lifecycle, by_channel, by_lead_source, reachability, duplicate_candidates), `contacts_search {q, lifecycle_stage, channel, lead_source, tag_id, limit≤100, offset}`.

## Appointments

`appointments_list {status[], kind[] test_drive|external|block|clinic, from, to, vehicle_id, owner_user_id, limit≤100}` — returns rows only, no cursor: use it to sample, not to count thousands. REST `appointments_list` via `call_operation` adds `lead_id, contact_id, appointment_type_id` and a cursor. Clinics: `clinic_agenda_list`, `clinic_services_list` (entry services flag which bookings count as first visits).

## Ads join

With the add-on: `ads_overview_get`, `ads_performance_list {by}`, `ads_funnel_get`, `call_operation ads_stages_list` (writing→booked→attended→paid with reference band and `weakest`), `ads_report_list` (`tail` = non-ad conversations). See the `vitrina-ads` skill for meanings.

## Blind spots to state when relevant

No cost per lead anywhere; no true time-in-stage; ads invisible in `source`; `insights_leads.open` is a snapshot; `leads_*` analytics are all-time; `appointments_list` truncates silently; insights `recent`/`breaches` carry names.
