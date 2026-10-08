# Working on this repo

Every folder under `skills/` is one skill: `SKILL.md` (frontmatter `name` + `description`, body under 500 lines) plus optional `references/` (loaded on demand, pointed at from the body with the condition for reading each), `scripts/` (deterministic work the agent runs instead of re-deriving) and `agents/openai.yaml` (Codex picker metadata; add `policy.allow_implicit_invocation: false` only for a skill that also sets `disable-model-invocation: true`). `skills/` is flat on purpose: a single path serves every harness's plugin manifest.

Every skill must be listed in `.claude-plugin/plugin.json` (`skills` array) and in `README.md` under **Model-invoked** or **User-invoked**, with its name linked to its `SKILL.md`. Bump `.claude-plugin/plugin.json`'s `version` on every change to a shipped skill — installed users see an update when that number moves.

Before committing: `claude plugin validate . --strict` (a root `CLAUDE.md` is rejected, which is why these rules live in `AGENTS.md`) and, for each skill, `python3 -I <anthropics/skills clone>/skills/skill-creator/scripts/quick_validate.py skills/<name>` (checks the frontmatter against the Agent Skills spec: kebab-case name ≤ 64 chars, description ≤ 1024 chars, no angle brackets). Quote a description that contains a colon.

Writing rules: follow `writing-for-agents` (mattpocock) — ordered steps with completion criteria in `SKILL.md`, reference pushed behind pointers, one source of truth per fact, no restating what the environment already says. The skills must work for anyone with a Vitrina workspace and an API key: no customer names, no absolute paths, no credentials, no founder-only access in the main path — direct-database material is clearly labelled "Vitrina staff" and parametrised through environment variables.

`scripts/link-skills.sh` symlinks every skill into `~/.claude/skills` and `~/.agents/skills` (and any extra directory passed as an argument) for local development; a `git pull` then updates them.
