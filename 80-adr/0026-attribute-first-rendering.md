# ADR 0026: Attributes first, pixels second: the vault record is the truth and the photo is evidence

**Status:** Accepted
**Date:** 2026-10-21
**Deciders:** Testimony (backend and AI)
**Stage:** MVP

## Context

A person's photo of a piece may be blurry, crooked, cluttered, or a photo of them wearing it. If the engine trusted pixels, a bad photo would block an item from every look, and a model reading it could invent what it cannot see.

## Decision

The vault item record (category, colours, cloth, formality) is the source of truth for what the engine does. A photo is evidence for it: colours are read from it as a *suggestion* the person confirms (`ase/app/fabric/colours.py`), and a cut-out quality gate (`ase/app/fabric/cutout.py`) decides only whether the person's own pixels may appear in a composite: `clean`, `attributes_only` or `retake`. A bad cut-out never removes an item from styling.

## Rationale

It keeps styling correct when photos are not, makes every decision explainable from stored facts, and lets the person fix a wrong colour in one tap instead of retaking a photo.

## Consequences

**Positive:** robust to bad uploads; no model needed to read a photo. **Negative:** colour suggestions can be wrong on worn photos (skin and background), so they are only ever offered, never saved. **Reversal:** low.
