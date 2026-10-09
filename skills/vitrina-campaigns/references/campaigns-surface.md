# Campaigns, templates, follow-ups — surface

## WhatsApp templates (tag beta; campaigns:read/write)
- MCP `whatsapp_templates_list {messaging_account_id?, status PENDING|APPROVED|REJECTED|IN_APPEAL|PAUSED|DISABLED}` — no limit, includes `param_spec` (large).
- `call_operation whatsapp_templates_create {messaging_account_id, name ^[a-z0-9_]+$, language es|es_CL, category MARKETING|UTILITY|AUTHENTICATION, body_text, header_text? | header_media?{format IMAGE|VIDEO|DOCUMENT, url}, footer_text?, buttons?[{type QUICK_REPLY|URL|PHONE_NUMBER|FLOW, text ≤25, …}], param_meta?, usage?}` → 201 PENDING. Media upload `whatsapp_templates_header_media_create` is multipart → REST only.
- `whatsapp_templates_sync_create {messaging_account_id}` refreshes statuses; `whatsapp_templates_category_check_create` predicts reclassification; `whatsapp_template_param_binding_update`, `whatsapp_template_infer_bindings_create`; categories (usage) `whatsapp_templates_categories_list/create`, `whatsapp_template_usage_update` (deleting a category re-files under `other`).

## Campaigns (REST tag interna → REST only; MCP has list/stats/pause/resume)
- MCP: `campaigns_list {status?, limit ≤50}`, `campaign_stats {campaign_id}` (campaigns:read); `campaign_pause` / `campaign_resume {campaign_id}` (campaigns:write).
- REST (campaigns:write; no messages:send needed): `POST /campaigns {name, channel whatsapp|email|voice, audience_id, messaging_account_id, template_id, template_params{slot:{source contact_field|static, field?, value?, fallback?}} (header_media must be {source:'static', value:<https url>}), content?, reply_mode?, scheduled_at?}`, `PATCH|DELETE /campaigns/:id`, `POST /:id/test-send {recipients[1..5]}`, `/:id/schedule {scheduled_at}`, `/:id/send`, `/:id/cancel`; `GET /:id/recipients` (campaigns:read).
- Audiences: MCP `audiences_list {}` (no counts), `audience_counts {audience_id}`; REST `/audiences` CRUD (campaigns:write), preview/members (+contacts:read).

## Sends that reach customers
- `conversation_messages_create`, `conversation_templates_create`, `conversation_flows_create`, `conversation_location_create`, `conversation_attachments_create`, `conversation_voice_create`, `POST /conversations/email` → `conversations:write` + `messages:send`.
- Without messages:send: campaign send/schedule/test-send/resume (campaigns:write), `outbound_approvals_approve {id, message?, subject?, note?}` (outbound_approvals:write + campaigns:write), `followups_recontacto_run` (when campaigns:write held), `followups_subscribe` (future message), `clinic_waitlist_add` (automatic offers), MCP `appointments_cancel` (messages the patient).
- Policy: API keys → loop guard (same content to >20 contacts/10 min or >60 sends/min → 409 `OUTBOUND_WARNING`, repeat with `acknowledge`; 422 `OUTBOUND_BLOCKED`). Connected apps → fan-out rule (>3 distinct contacts/10 min → 202, parked in approvals).
- Approvals: `outbound_approvals_list {rail service_lifecycle|recontacto|seguimiento|campaign|first_touch|api|budget_followup, assignee_user_id?, limit?}`, `_get`, `_approve`, `_reject {id, reason?}`; holds `outbound_holds_list/get/sla_breaches/place/acknowledge/resolve`.

## Follow-ups and recontacto (MCP; REST interna)
- `followups_list`, `followups_overview` (followups:read); `followups_create {name, description, trigger_key, active?}` (followups:write); `followups_update` / `followups_delete` (followups:manage); `followups_subscriptions_list {contact_id}`; `followups_subscribe {followup_id, contact_id, conversation_id?, criteria?, fire_at?, preferred_channel?, fulfiller_kind ai_agent|human_self}`; `followups_subscription_cancel {id}`; `followups_channels_get` / `_set {whatsapp, email}`.
- Recontacto: `followups_recontacto_config {enabled, daily_cap, lost_lookback_days, max_evaluations_per_step, re_evaluation_after_days, min_hours_between_touches, excluded_template_ids}` (followups:write; `enabled:true` also campaigns:write; a call with no fields reads but still needs write), `followups_recontacto_preview`, `_readiness` (read), `_run` (write; auto-sends with campaigns:write), `_attempts {status?, situation?}` (≤200), `_stats {since_days}`, `_template_draft` (writes nothing). Lead reviewer: `followups_lead_review_config {enabled, stage_autonomy auto|suggest, auto_confidence, instructions, half_life_days}`.

Size traps: `whatsapp_templates_list` (no limit, param_spec), `email_template_get`, `whatsapp_flow_get` (design blobs).
