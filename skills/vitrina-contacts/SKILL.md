---
name: vitrina-contacts
description: "Keep a Vitrina workspace's contact directory clean and usable over MCP/REST: search and inspect contacts, find and merge duplicates, import a CSV with a dry-run plan, set legal identity (RUT) and address, record consent and opt-outs, disable the bot for a person, tag and segment, count who is marketable before a campaign, and read or fix custom attributes. Use when the user asks about contactos, duplicados, importar una planilla/CSV, RUT, consentimiento, opt-out, 'no le respondas más el bot', etiquetas, segmentos, cuántos contactos puedo contactar, campos personalizados — even without the word 'contact'."
---

# Contacts

A contact is one person with channels (WhatsApp, Instagram, email…), a lifecycle stage (`unknown → prospect → qualified_prospect → customer → repeat_customer → inactive | blocked`), legal identity, address, consent ledger and custom attributes; conversations, leads, appointments and payments hang off it. There is no list endpoint and no delete: you search, you merge, you archive or block. Merges are irreversible. Tools and exact inputs: [`references/contacts-surface.md`](references/contacts-surface.md). Scopes `contacts:read` / `contacts:write` (+ `tags:*`, `custom_attributes:*` for taxonomy). On a connector, writes need the «Contactos» pack; tag definitions and tags on conversations need «Conversaciones» (`tags:write`); custom attribute definitions need «Configuración del inbox». `Unknown operation` from `describe_operation` = pack missing: tell the user to add it in Vitrina → Configuración → Conectar tu IA (MCP) → Apps conectadas → «Editar permisos» (no reconnect; only the member who connected the app can add it).

## Step 1 — Know the directory

`contacts_stats {}` (total, by lifecycle, by channel, by lead source, email/phone reachability, duplicate candidates) and `contacts_marketable_count {}` (valid email + consent + subscribed, not merged/archived/blocked). Then `contacts_search {q | lifecycle_stage | channel | lead_source | tag_id, limit}` for the people the question is about; `contacts_get {id}` returns `null` for a missing id, not an error.

Done when: the question has numbers behind it and a sample of the rows involved.

## Step 2 — Duplicates

`contacts_duplicates {}` (clusters sharing a lowercased email or digits-only phone, up to 100 with full rows) or `contacts_suggest_duplicates {id}` for one person. Decide the survivor by the richer record (channels, leads, payments), then `contacts_merge {primary_id, secondary_ids}`: everything moves to the survivor, empty fields are filled, secondaries become tombstones (`merged_into_contact_id`). **Confirm the list with the user before merging more than a handful**; there is no unmerge. A family sharing one phone is not a duplicate — leave it and note it (the agent's identity logic handles it).

Done when: each cluster is merged, kept with a reason, or listed for the user to decide.

## Step 3 — Import

`call_operation contacts_import_create` with `csv` (RFC 4180, ≤ 10 MB, optional `mapping`) or `rows` (≤ 20,000) and **`dry_run:true` first**: the plan classifies each group as create | merge | ambiguous | invalid | skip | duplicate_in_file by normalised phone, lowercased email and external id. Show the counts and the ambiguous groups, get decisions, then commit with `decisions`; a group changed since the review is refused as `stale_plan`. `conflict_policy` keep_existing (default) | overwrite (phone, email, external id are never overwritten). Consent is granted only with `email_consent_attested:true` and only when the user asserts it. `POST /contacts` does not dedupe; only import does.

Done when: the plan was reviewed, the commit returned the created/merged counts, and the ambiguous groups are either decided or listed.

## Step 4 — Identity, consent, bot

Legal identity `contacts_set_legal_identity {contact_id, tax_id, tax_id_kind: rut|passport|foreign_tax_id, person_kind, …}` (RUT check digit verified; `tax_id_taken` names the conflicting contact → that is a duplicate to merge first). Address `contacts_set_address {contact_id, comuna_code (5-digit CUT), …}`. Outbound consent is an append-only ledger: `contacts_record_outbound_preference {contact_id, channel, scope: marketing|service|promised_followup|all_proactive, status: allowed|blocked|unknown, legal_basis?, evidence_message_id?}`; `contacts_bulk_consent {contact_ids}` for attested lists; a customer's own opt-out can never be lifted through the API — say so. `contact_suppress {channel, identifier}` blocks an identifier outright (a different system from preferences). `contacts_set_bot_replies_disabled {contact_id, value:true}` makes the AI stay silent for that person (staff, VIPs, a complaint being handled by a human).

Done when: every identity or consent change names the contact, the field, the evidence, and the write that applied it.

## Step 5 — Tags, segments, attributes

`contact_tag_add {contact_id, tag_name}` (creates on attach; connector `call_operation contact_tags_create {params:{id}, body:{tag_id | name}}`), `contacts_tags_bulk_create {contact_ids ≤500, tag:{name}}` via `call_operation`; tag definitions `tags_create`, `tag_replace`, `tag_delete`; tags on a conversation `conversation_tags_create` / `conversation_tag_delete`; search by `tag_id`. (`tags_suggest_list` is model spend and not available to a connector.) Custom attribute definitions `custom_attributes_list/create {entity_type, data_type: text|number|boolean|date|select|multiselect|url|email|file|rut}`; values `contact_attributes_replace {attributes:[{key,value}]}`; a `file` attribute takes a JSON body `call_operation contact_attribute_file_create {params:{id, key}, body:{filename, content, content_encoding: utf8|base64, content_type?}}` (the attribute must already be defined as `file`; keep one MCP call under ~1 MB); `custom_attributes_undefined_keys` finds values written under keys nobody defined; `custom_attributes_purge_values` is irreversible. Lifecycle stage changes go through `contact_update`.

Done when: the segment exists as a tag or a searchable attribute and the count matches what the user expects.

## Step 6 — Report

Numbers before/after, every irreversible action listed with ids, what was left for the user to decide, and the privacy line: contact rows carry names, phones and RUT — keep exports local, never paste them into tickets or chats.
