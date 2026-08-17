# Architecture Decision Records

**Format:** MADR. **Status:** all Accepted as of 2026-08-17.

ADRs are immutable once accepted. A decision changes by writing a new ADR that supersedes the old one — never by editing it. If you are explaining *why* for the third time in prose, it wants an ADR.

| # | Decision | Reversal cost |
|---|---|---|
| [0001](0001-two-services-gateway-and-ase.md) | Two services now, four more designed | Low |
| [0002](0002-spree-and-notify-as-modules.md) | spree and notify are modules, not services | Low |
| [0003](0003-no-root-git-per-service-repos.md) | No repository at the workspace root; every service is standalone | Moderate |
| [0004](0004-single-alembic-project-in-faue-db.md) | One Alembic project and one model package in faue-db | Low |
| [0005](0005-single-venv-pip-tools.md) | Single root virtualenv managed with pip and pip-tools | Low |
| [0006](0006-openrouter-tier-addressed-llms.md) | OpenRouter for LLMs, addressed by task and tier, never by model name in code | Low |
| [0007](0007-pluggable-embeddings-self-hosted-default.md) | Pluggable embedding providers with a self-hosted default | Low (provider), moderate (vectors) |
| [0008](0008-closed-set-model-policy.md) | Closed-set policy: models act within a rule-defined legal pool | N/A — safety decision |
| [0009](0009-pluggable-look-rendering.md) | Look rendering is a pluggable strategy; generative is the default | Low |
| [0010](0010-defer-catalog-and-affiliate.md) | Defer the cross-brand catalog and affiliate loop to M1-2 | Low |
| [0011](0011-six-question-style-dna.md) | Style DNA is six questions, taxonomy defined by FAUE | Low |
| [0012](0012-consent-denied-by-default.md) | Every consent purpose defaults to denied, enforced by a shared dependency | N/A — legal obligation |
| [0013](0013-server-authoritative-image-pii-pipeline.md) | Image PII redaction is server-authoritative | N/A — privacy obligation |
| [0014](0014-untrusted-content-trust-tiers.md) | All external content is untrusted input to models | High to loosen |
| [0015](0015-railway-first-vps-later.md) | Deploy on Railway first; evaluate a VPS on cost | Low |
| [0016](0016-magic-link-authentication.md) | Email magic link as the primary credential | Low |
| [0017](0017-model-led-assembly.md) | Models select and assemble looks within the legal pool | Low |
| [0018](0018-generative-rendering-default.md) | Generative rendering is the default strategy | Trivial |
| [0019](0019-remove-instagram-integration.md) | Remove the Instagram integration | Low |
| [0020](0020-style-library-licensed-not-scraped.md) | Style library imagery is licensed or generated, never scraped | High if violated |
| [0021](0021-workspace-tenancy-model.md) | Workspace tenancy from the first migration | Low |
