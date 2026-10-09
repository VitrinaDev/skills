---
name: vitrina-api-integrator
description: "Integrate an external system with Vitrina's API: discover and call any published operation (search_operations → describe_operation → call_operation, or REST with the TypeScript SDK), authenticate with API keys and scopes (sk_, sk_test_, pk_ publishable keys for widgets), subscribe to webhooks with signature verification and retries, use idempotency keys, respect rate limits, paginate correctly, and read the error envelope. Use when the user is a developer asking how to 'conectar mi sistema', 'crear contactos desde mi CRM', 'recibir un webhook', 'cuál endpoint uso', 'API key', 'SDK', 'OpenAPI', rate limit, 'integrar con Vitrina', or wants code that talks to Vitrina — even without the word 'API'."
---

# Integrate with Vitrina's API

One contract, two transports (ADR 0106): REST at `https://api.vitrinadev.com/api/v1/…` and the same operations over MCP through three generic tools. Everything published is tier `beta` (changes come with a changelog entry); `interna` operations serve the UI and are reachable over REST with the scope but never through `call_operation`. Reference: [`references/api-surface.md`](references/api-surface.md). Public docs: `https://docs.vitrinadev.com` (chapters `empezar`, `autenticacion`, `webhooks`, `errores`, `sdk`, `sandbox`, `mcp/*`, one chapter per domain).

## Step 1 — Find the operation

`search_operations {query?, tag?, limit}` (every word of `query` must match id, path, tag or summary; `tag` is exact, e.g. `"Contacts"`), then `describe_operation {operation_id}` for parameters, body schema, scopes, tier and destructive flag. Operation ids derive from the path: `<nouns>_<verb>` with the noun before a `{param}` made singular and the verb `get` (path ends in a param) | `list` | `create` (POST) | `replace` (PUT) | `update` (PATCH) | `delete` — `contacts_search_list`, `contact_get`, `contact_merge_create`; the raw `"GET /contacts/{id}"` form is accepted. "Unknown operation" means interna, sensitive, out of scope, wrong vertical, or a write pack not granted — the message is deliberately identical.

Done when: you have the operation id, its required params, scope and whether it writes.

## Step 2 — Credentials

An `sk_` API key (Settings → Claves de API, or `api_keys_create {name, scopes, expires_at?, livemode?}` with scopes ⊆ the minter's own) sees the full MCP catalogue and every REST route its scopes allow. `livemode:false` mints an `sk_test_` key bound to a sandbox (409 `SANDBOX_NOT_PROVISIONED` until `POST /sandbox/clinic|automotive`). Rotation `api_key_rotate_create {grace_period_hours ≤72}`; scopes are immutable, mint a new key. Browser-side: a `pk_` publishable key (REST `/publishable-keys`, fixed scopes `stock:read, leads:intake, widget:chat, appointments:intake, storefront_events:write`, origin allowlist) for the `/widget/*` routes only. A connected app's OAuth token is a read-only connector unless write packs were ticked. Never put an `sk_` key in a browser or a repo.

Done when: the integration has the narrowest key that works, with an expiry, and the test/live split is decided.

## Step 3 — Call it right

REST: `Authorization: Bearer sk_…`, JSON bodies, responses `{data, meta}`; errors `{error:{code, message, requestId, details?, field_errors?}}` — branch on `code`, quote `requestId` when asking Vitrina. Pagination is mixed per route: cursor (`limit ≤100`, `cursor`, `meta.pagination.nextCursor`), offset (`limit`/`offset`, `meta.total`) or page (`page`/`limit ≤200`) — read `describe_operation`. Display ids (`C-12`, `L-3`, `A-8`) work in paths only, never in bodies. Rate limit 120 req/min per key (`X-RateLimit-Remaining`, 429 + `Retry-After`; tenant override exists). Idempotency: `Idempotency-Key` (8–200 chars, 24 h, per credential) on POSTs to published operations; replay returns `X-Idempotent-Replay: 1`, same key + different body → 409. `call_operation` adds a default key to every non-GET and refuses undeclared params, bodies on GET, and multipart (uploads go over REST). SDK: `@vitrina/api` (`createClient({baseUrl, apiKey})`, typed from `openapi.public.json`, served at `GET /api/v1/docs/openapi.json`).

Done when: a first call succeeds end to end with the real key and the error path (401, 403 missing scope, 404 cross-tenant = missing, 422 validation) has been exercised once.

## Step 4 — Webhooks

`webhooks_create {url, events[1..20], description?}` (MCP creates notice-only subscriptions; REST `include_data:true` ships the payload) returns the `whsec_…` secret **once**. Verify `X-Webhook-Signature: t=<unix>,v1=<hex>` = HMAC-SHA256(secret, `${t}.${rawBody}`) within 300 s; dedupe on `X-Webhook-Event-Id`; answer 2xx fast. Retries 5× at 5/10/20/40/80 s; after 20 consecutive failures or 24 h failing the subscription pauses (`webhook_resume_create`); deliveries and redelivery over REST (`webhook_deliveries_list`, `webhook_delivery_redeliver_create {deliveryId}` — an integer). Catalogue with samples: `webhooks_events_list` (large). If the key that owns the subscription is revoked, payloads arrive with `data_omitted: owner_unavailable` — recreate the subscription with the new key.

Done when: the endpoint verifies signatures, is idempotent on event id, and the first real event was received.

## Step 5 — Hand over

Write the integration note: operations used (ids + scopes), key name and expiry, webhook events and endpoint, idempotency strategy, pagination style per list, and the support line (requestId + timestamp + key prefix). Code goes in the user's language and framework; secrets in their secret store, never in the note.
