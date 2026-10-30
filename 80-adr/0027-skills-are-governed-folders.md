# ADR 0027: Skills are folders with governed references, loaded a phase at a time

**Status:** Accepted
**Date:** 2026-10-21
**Deciders:** Testimony (backend and AI)
**Stage:** MVP

## Context

Prompts as loose strings cannot be reviewed, versioned or evaluated, and cultural knowledge buried in a prompt has no named owner.

## Decision

Each skill is a folder (`ase/skills/<name>/`): an entry file, ordered phase files naming the references each needs, and reference files with an owner and a **named reviewer**. The runner loads only the active phase and the references it lists, checks them at load (handlers must live in `app.skills`; untrusted text may appear only inside a `<data>` block; a model phase has a router task and a template fallback), and returns a provenance record: the skill version (a hash of the folder), each phase's hash, who answered (code, model, cache or template), and the hash of every reference loaded. In production a reference without a named reviewer, or an approval for its exact hash, is not loaded.

## Rationale

The folder is the unit a reviewer can read, a change can version, an eval can cover and an incident can trace. Progressive disclosure keeps tokens for the phase that needs them.

## Consequences

**Positive:** every answer traces to the exact text and rules that produced it. **Negative:** more files than a prompt string; a new skill is a new folder with the same shape. **Reversal:** moderate; the shape is cheap, the content is the asset.
