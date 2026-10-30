# ADR 0025: The default renderer is the deterministic composite; new people see reviewed archetype looks

**Status:** Accepted; supersedes [0018](0018-generative-rendering-default.md)
**Date:** 2026-10-21
**Deciders:** Testimony (backend and AI)
**Stage:** MVP

## Context

ADR 0018 made generative rendering the default so a first-session user sees a complete look. In the render pilots (2026-10-16 to 10-19) the small image models drew labels, changed garments, and mis-drew gele, aso oke and adire; each image costs money or free-tier allowance and takes seconds; and a generated picture of an owned piece is no longer that piece.

## Decision

`composite` is the default: the person's own cut-out pieces on a flat-lay template, deterministic and free. A person with an empty wardrobe sees reviewed **archetype looks** (style cards, `ase/app/archetypes`), each approved by a named reviewer for its tradition at its exact content hash. `generative` stays selectable and is never used for an owned look, because it can change the piece.

## Rationale

The first view must be correct before it is beautiful: an agbada that is not an agbada is worse than a plainer picture of a real one. Archetypes are reviewed once, rendered once, and reused by everyone, which is cheaper and safer than drawing per request. Generative remains for cases that want imagination rather than fidelity.

## Consequences

**Positive:** zero marginal render cost; fidelity to owned pieces; cultural content passes a human before it is shown. **Negative:** composites look plainer than generated art until the cut-out quality improves; archetypes need reviewers and a rendered image set before production shows any (until then production shows none). **Reversal:** trivial; `renderer.default` is configuration.
