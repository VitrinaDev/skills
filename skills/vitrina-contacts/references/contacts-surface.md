# Contacts surface

Hand-written MCP tools (plain `sk_` key) — id field names vary: `contacts_get {id}`, `contacts_merge {primary_id, secondary_ids[1..50]}`, most others `{contact_id}`.

| Tool | Inputs | Scope |
|---|---|---|
| `contacts_search` | `q?, exclude_id?, include_merged?, limit ≤100 (25), offset?, lifecycle_stage? (CSV list), channel?, lead_source?, tag_id?, company_id? ('none' = no company)` | contacts:read |
| `contacts_stats`, `contacts_duplicates`, `contacts_marketable_count` | none | contacts:read |
| `contacts_get {id}` (null when missing), `contacts_suggest_duplicates {id}`, `contacts_list_outbound_preferences {contact_id}` | | contacts:read |
| `contacts_merge {primary_id, secondary_ids}` | irreversible; emits `contact.merged` | contacts:write |
| `contacts_set_legal_identity {contact_id, tax_id, tax_id_kind rut|passport|foreign_tax_id, person_kind natural|juridica, legal_name?, giro?, representative_contact_id?}` | `juridica` needs legal_name + giro + representative; `""` refused, `null` clears; `tax_id_taken` → `conflicting_contact_id` | contacts:write |
| `contacts_set_address {contact_id, comuna_code, address_street, address_number, address_unit?}` | | contacts:write |
| `contacts_set_bot_replies_disabled {contact_id, value}` | | contacts:write |
| `contacts_record_outbound_preference {contact_id, channel whatsapp|email|voice|any, scope marketing|service|promised_followup|all_proactive, status allowed|blocked|unknown, legal_basis?, evidence_message_id?, expires_at?}` | append-only ledger | contacts:write |
| `contacts_bulk_consent {contact_ids ≤1000}` | | contacts:write |
| `contacts_upload_attribute_file {contact_id, attribute_key, filename, content_base64, mime_type?}` | ≤ 25 MB — a token trap | contacts:write |
| `contact_tag_add {contact_id, tag_name ≤60}`, `contact_suppress {channel whatsapp|email, identifier, contact_id?}` | | contacts:write |
| `contact_completeness_check {contact_id, purpose}` | automotive only | contacts:read |
| `custom_attributes_undefined_keys {entity_type contact|conversation}`, `custom_attributes_purge_values {entity_type, key}` (irreversible) | | custom_attributes:* |

`call_operation` (tag Contacts, beta; ids follow `<nouns>_<verb>`): `contacts_create` (only `name` required; no dedupe), `contact_update` (PATCH: lifecycle_stage, name, email, phone, language, country, company_id, …), `contact_tags_create {tag_id|name}`, `contact_tag_delete {tagId uuid}`, `contacts_tags_bulk_create {contact_ids ≤500, tag:{tag_id|name}}`, `tags_list/create`, `tag_replace`, `contact_channels_*`, `contact_notes_*`, `contact_timeline_list`, `contact_conversations_list`, `contact_block_create {value}`, `contact_archive_create {value}`, `contact_report_spam_create`, `contact_bot_replies_disabled_create`, `contact_team_account_create`, `contact_outbound_preferences_list/_create` (REST also accepts instagram, messenger), `contact_attributes_list`, `contact_attributes_replace {attributes:[{key,value}] 1..50}`, `contact_attribute_delete`, `custom_attributes_list/_create {entity_type contact|conversation|ticket|company, data_type …}`, `custom_attribute_delete {purge_values?}`, `contacts_import_create`, `contacts_export_list` (whole directory as CSV text — large), `contacts_marketable_count_list`.

Import (`contacts_import_create`): exactly one of `csv` (RFC 4180, ≤10 MB, `mapping?`) or `rows` (≤20,000); `dry_run:true` → plan with groups `create|merge|ambiguous|invalid|skip|duplicate_in_file`; commit with `decisions` per group; `stale_plan` when a group changed; `conflict_policy keep_existing|overwrite` (phone/email/external_id never overwritten); `email_consent_attested:true` is the only consent grant. `describe_operation contacts_import_create` is large.

Contact row: id, external_id, name, email, phone, language, country, brand, lifecycle_stage, job_title, birthday, city, company_id, social, email_consent, email_status, origin_channel, imported_from, merged_into_contact_id, merged_at, blocked_at, archived_at, spam_at, bot_replies_disabled_at/_by, tax_id, tax_id_kind, person_kind, legal_name, giro, representative_contact_id, address_*, comuna_code, region_code; computed: display_name, named, channels[], lead_sources[]. No display id. Marketable = valid email + `email_consent` + `email_status = subscribed`, not merged/archived/blocked. Suppression (`contact_suppress`) and outbound preferences are two systems; opt-out lifting is member-only in the UI.

Webhooks for integrators: `contact.created|updated|merged`.
