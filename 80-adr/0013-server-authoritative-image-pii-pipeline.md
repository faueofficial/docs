# ADR 0013: Image PII redaction is server-authoritative

**Status:** Accepted
**Date:** 2026-08-17
**Deciders:** Testimony (backend and AI)
**Stage:** all

## Context

FAUE's core flows require users to photograph fabric, clothing, and outfits. Those photographs routinely contain faces, GPS coordinates in EXIF, and readable personal text. Images are sent to third-party model providers and rendered into shareable cards.

## Decision

Every user-supplied image passes a server-side pipeline before storage, sharing, or model use: safety classification, EXIF strip, face detection and irreversible redaction, OCR scan and text redaction, and disposal of the original by default. Per-asset flags record each step. The client may blur for preview quality; the server repeats every step and treats client output as untrusted.

## Rationale

A client-side blur is a user-experience feature, not a privacy control — the unredacted image still crosses the network and can be intercepted, and a modified client simply skips it.

EXIF GPS is the most common silent location leak in any photo-upload product, and it is invisible to users. Face redaction runs on an in-process open model rather than a vendor call, because sending an unredacted face to a third party in order to detect the face defeats the purpose.

Recording pipeline outcomes per asset makes compliance queryable and turns a pipeline bug into something visible rather than silent.

## Consequences

**Positive:** Provable compliance. A leaked derivative contains no faces, no coordinates, and no readable personal text. A bug is detectable by querying the flags.

**Negative:** CPU cost on every upload, additional latency before an image is usable, and a heavier deployment for the detection model. False positives blur things that were not faces.

**Reversal cost:** Not applicable — this is a privacy obligation.

## Alternatives considered

Client-side only — rejected as not a control. Vendor face detection — rejected because it requires sending the unredacted image to a third party.

---

*ADRs are immutable once accepted. To change this decision, write a new ADR that supersedes it.*
