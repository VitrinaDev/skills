---
name: analyze-business
description: "End-to-end analysis of a Vitrina workspace to research a business and draft its AI agent package (instructions + skills + KB). Corpus mode when the workspace has imported conversation history (WhatsApp coexistence) - export, subagent fan-out for tone/flows/knowledge, contact-data mining into an import CSV, billable classification with the close-analyzer prompt, monthly billing and model-cost estimate. Interview-only mode when the number is new - structured analysis of interview transcripts, PDFs and notes into the same drafting inputs. Use whenever the user wants to analyze a client's or workspace's conversations or interviews, onboard a new business, \"build the agent for X\", \"analyze X's chats\", \"procesa la entrevista de X\", extract customer data from conversations, run a billable analysis, or estimate what a workspace will pay - even if they only name the business (\"help me with the X agent\", \"haz el análisis de la clínica X\")."
---

# Analyze a business from its conversation corpus

Repeatable pipeline first used for a dental clinic in 2026-08. If a previous package exists in your working directory (`<slug>-agent/`), consult it whenever a phase's expected output is unclear. Everything is read-only against prod; all data stays local and contains PII (never publish or commit the export).

The pipeline is modular. The user may want only one phase ("solo el análisis billable") — ask nothing, just run the phases their request implies. Full onboarding = all phases in order.

## Phase 0 — Inputs

- **Tenant**: slug, name, or UUID (production database, read-only; the export script reads `VITRINA_SUPABASE_PROJECT_REF` and the Supabase CLI token from the macOS keychain — Vitrina staff only).
- **Business context**: any interview transcripts/PDFs/notes the user has (usually in a `<slug>-agent/` folder under the working dir). Read them fully yourself — they define what the owner *asked for*; the corpus defines what the team *actually does*; when they conflict, **the corpus wins and the contradiction gets flagged**.
- Create/reuse `<slug>-agent/` as the package folder. Layout: `export/`, `analysis/`, `skills/`, `knowledge/`, plus `instructions.md`, `SETUP.md`, `TOOLS-PROPOSAL.md`, `TOOLS-COVERAGE.md`, `BILLING-ESTIMATE.md`, `PITCH-<dueño>.md`, `contacts-import-draft.csv`, `README.md`.

Also snapshot the workspace state in prod (informs SETUP + tools docs): tenant `vertical`, `messaging_account` rows, provisioned `function` rows, integration accounts (e.g. `healthatom_account`), existing `ai_agent`/`skill` rows. One SQL round-trip each via the same curl pattern as the export script.

**Mode check (decides the rest of the pipeline):** count the tenant's conversations/messages in the same snapshot. A meaningful corpus (hundreds of conversations from a coexistence import) → run Phases 1–4. A new WhatsApp number (zero or a handful of conversations) → **interview-only mode**: skip Phases 1–4 entirely and follow the section below; there is nothing to export, no tone corpus, no contacts to mine, no billable history.

## Phase 1 — Export (script)

```bash
python3 scripts/export_tenant.py <slug-or-uuid> <pkg>/export
python3 scripts/build_batches.py <pkg>/export <BUSINESS-LABEL>   # ~230KB balanced batches
```

Notes: curl-based on purpose (python urllib gets Cloudflare-403'd). Message content capped at 4,000 chars. `[image]/[file]` placeholders for media.

## Phase 2 — Corpus analysis (workflow fan-out)

Read `references/analysis-workflow.md` and launch that Workflow (adapted to the business): one **sonnet** extractor per batch writing `analysis/batch-NN.json`, then three **opus** synthesizers writing `TONO-Y-ESTILO.md`, `FLUJOS-Y-CASOS.md`, `CONOCIMIENTO-Y-TEMPLATES.md`. The synthesizers should re-verify counts by grepping the raw `messages.jsonl` — batch summaries alone drift.

Read all three syntheses yourself before drafting anything. The recurring findings that matter most (seen in every corpus so far):
- Real treatment (tú/usted) usually contradicts what the owner asked for — quantify and decide.
- Free-chat style ≠ template style (two registers; both are the brand).
- **Staff/internal chats mislabeled as customers** in the import — must be flagged and excluded from tone, and those contacts marked no-bot in SETUP.
- Prices drift over the period — every price needs a vigencia date and a single source (KB).
- Practices the bot must NOT replicate (legal/data-privacy red flags) — collect them explicitly.

## Phase 3 — Contacts CSV

```bash
python3 scripts/merge_contacts.py <pkg>/analysis <pkg>/contacts-import-draft.csv
```

Document the import path in SETUP.md: native CSV import takes only `name,email,phone,...`; RUT → `contact.tax_id` via API; domain fields → `contact_attribute`. Flags column needs human review before any import (no_contactar, deudores, staff).

## Phase 4 — Billable classification + billing estimate (scripts)

```bash
python3 scripts/billable_run.py <pkg>/export [channel]   # re-run until err=0 (resume-safe)
python3 scripts/billable_report.py <pkg>/export [--uf-per-conv 0.012 --in-price ... ]
```

Uses the platform's close-analyzer prompt (`src/agents/close-analyzer/instructions.md` in vitrina-app, located through `VITRINA_APP_DIR`) with `~deepseek/deepseek-v4-flash-latest`. Critical detail baked into the report: **months come from message dates, never `conversation.created_at`** (coexistence stamps everything with the import date). "Active billable per month" is the invoice proxy. Write the result as `BILLING-ESTIMATE.md`: billable %, monthly table, revenue at the tenant's per-conversation price, and the model-cost table with stated assumptions.

**Coverage/latency baseline** (the "AI answers in seconds" pitch, and the post-launch Insights baseline):

```bash
python3 scripts/coverage_report.py <pkg>/export --open 8 --close 20 \
  --staff-phones "+569...,..." --autoresp "sig1,sig2"
```

Volume heatmap (day×hour, local time), first-real-response latency by segment (in-hours / weekday nights / weekends), unanswered share, Monday-8am backlog. Two traps it already handles, but you must supply the inputs: pass the **staff phone numbers** (professionals chat on the same number in coexistence imports — find them via the contacts CSV flags + the professionals directory; verify by name, flag text alone has false positives) and the **autoresponder signature** (a template auto-reply is not a real response — counting it fakes instant out-of-hours coverage). Note in the report that low out-of-hours volume is *suppressed demand*, not absent demand. Write findings as `analysis/COBERTURA-Y-RESPUESTA.md`.

**Owner-facing pitch** — turn the baseline into `PITCH-<dueño>.md`: Spanish, WhatsApp-friendly, only numbers from THEIR corpus. Structure that works: (1) headline = total inquiries/month that go from waiting hours to seconds; (2) praise what the team already does well (the in-hours median — it's true and it lands the "the agent unclogs you, doesn't replace you" frame); (3) the brutal segment numbers (weekend 0%-answered-in-an-hour type facts); (4) never-answered and Monday-backlog; (5) suppressed demand as upside, closing with the owner's own ROI math from the sales interview. No feature talk — only their pains, measured.

## Interview-only mode (new WhatsApp number, no corpus)

When there is no history, the interview materials ARE the evidence base — process them with the same rigor the corpus would get:

1. Read every source fully yourself: call transcripts, onboarding-interview analyses, Brain/Wispr PDFs, catálogos, planillas, WhatsApp Business quick-replies the owner exports. (A good interview analysis covers: tone, scheduling rules, policies, prices, limits, metrics, open questions.)
2. Produce `analysis/ENTREVISTA.md` — the stand-in for the three corpus syntheses, with the same consumers in mind: (a) identity + tone decisions as **declared** (greeting, tú/usted, emojis, frases tipo — quote verbatim); (b) services/prices/durations with source; (c) operational flows as the owner describes them, step by step; (d) policies and hard limits; (e) escalation map (who decides what); (f) proactivity/metrics promises made in the sale; (g) **open questions** — everything the interview left undecided.
3. Draft the package (Phase 5) from that doc + the closest previous package for the same vertical, if you have one. Mark every tone and flow decision as **"declarado, no validado con conversaciones reales"** in SETUP.md — owners routinely mis-describe their own register (one clinic asked for tuteo, gave usted examples; its corpus said tuteo 80–94%).
4. Billing estimate: no measured volume — use the owner's declared numbers (atenciones/mes, personas/mes) with the same cost model, clearly labeled as declared. Skip `BILLING-ESTIMATE.md`'s classification section or omit the file.
5. Leave a **revisit hook** in SETUP.md and the project memory: 4–8 weeks after launch the number will have real conversations — re-run corpus mode (Phases 1–4) to validate tone, mine contacts, and true-up the billable estimate. That later pass is cheap and catches every declared-vs-real gap.

## Phase 5 — Agent package drafting

You (the main agent) write these — don't delegate the drafting; the syntheses are the evidence base.

- `instructions.md` — Spanish system prompt in the house format. Reuse the structure of the closest previous package for the vertical. Do NOT list tools or skill bodies — the harness injects the skills catalog (`load_skill` on demand), tool descriptions, channel guide and runtime context. Skills are NOT fully injected (only name+description).
- `skills/` — one playbook per operational flow from FLUJOS-Y-CASOS (frontmatter: `name`, `description` = when-to-use, `status: active`; body: Cuándo / Cómo numbered steps / Reglas). Templates the team uses verbatim live INSIDE the skill that uses them.
- `knowledge/` — static citable docs only (prices with vigencia marks, policies, location, payment data verbatim, directory). KB is vector-retrieved: never put step-by-step procedures there.
- `TOOLS-PROPOSAL.md` + `TOOLS-COVERAGE.md` — map measured demand (grep intent counts over customer messages) → tools needed → exists/gap. Check the current tool registry (`GET /ai-agents/tools-catalog` or `src/tools/registry.ts`), not memory — tool sets change.
- `SETUP.md` — evidence-backed decisions, apply checklist (nothing auto-applied to prod), simulator test scenarios, open questions for the owner.

Finish by saving/updating a project memory (`project_<slug>_agent.md`) with tenant id, package location, key decisions and blockers.

## Hard rules

- **Never write to prod.** Everything is drafts on disk; the user applies via UI/API when ready.
- PII stays local: `export/`, `analysis/batch-*.json` and the contacts CSV never leave the machine.
- Every number you present should be recomputable: keep the scripts' output in the docs.
