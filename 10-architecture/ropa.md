# Record of Processing Activities

**Stage:** MVP · **Controller:** FAUE · **Contact:** faueofficial@gmail.com
**Last reviewed:** 2026-08-17 · **Review cadence:** quarterly and on any schema change

Required by GDPR Article 30 and the equivalent NDPA provisions. **Anything not in this register may not be collected.** A new field without a row here fails review.

Bases: `contract` · `consent` · `explicit consent` (sensitive) · `legitimate interest` · `legal obligation`.

---

## gateway.users

| Field | Class | Basis | Retention | Leaves system |
|---|---|---|---|---|
| `id` | Pseudonymous id | Contract | Life of account | Yes — pseudonymous, to analytics |
| `status` | Operational | Contract | Life of account | No |
| `age_verified` | Operational | Legal obligation | Life of account | No |
| `created_at` | Operational | Contract | Life of account | No |
| `deleted_at` | Operational | Legal obligation | 7 years | No |

## gateway.auth_identities

| Field | Class | Basis | Retention | Leaves system |
|---|---|---|---|---|
| `provider`, `provider_uid` | Identifier | Contract | Life of account | No |
| `email_enc` | Direct identifier | Contract | Life of account | Yes — email provider only |
| `email_bidx` | Derived identifier | Contract | Life of account | No |
| `phone_enc` | Direct identifier | Contract | Life of account | Yes — SMS provider (`M1-2`) |
| `display_name` | Direct identifier | Contract | Life of account | No |
| `last_used_at` | Operational | Legitimate interest | Life of account | No |

## gateway.refresh_tokens

| Field | Class | Basis | Retention | Leaves system |
|---|---|---|---|---|
| `token_hash`, `family_id` | Credential | Contract | 30 days past expiry | No |
| `user_agent` | Operational | Legitimate interest (security) | 30 days past expiry | No |

## gateway.profiles

| Field | Class | Basis | Retention | Leaves system |
|---|---|---|---|---|
| `username` | Direct identifier | Contract | Life of account | Yes — on public share pages |
| `display_name` | Direct identifier | Contract | Life of account | Yes — on share cards |
| `gender_presentation` | Personal | Consent (`personalization`) | Life of account | No — informs constraints only |
| `city` | Coarse location | Consent (`location_weather`) | Life of account | No |
| `geohash5` | Coarse location (~5 km) | Consent (`location_weather`) | Life of account | Yes — to weather provider, without any identifier |
| `locale`, `currency` | Preference | Contract | Life of account | No |
| `avatar_asset_id` | Reference | Consent (`camera_photos`) | Life of account | No |

## gateway.body_profile

**Sensitive category. Explicit consent required for every field. Never leaves `gateway` in raw form.**

| Field | Class | Basis | Retention | Leaves system |
|---|---|---|---|---|
| `body_shape` | Sensitive | Explicit consent | Until deleted | No — abstracted to constraints |
| `height_cm_enc` | Sensitive | Explicit consent | Until deleted | No |
| `measurements_enc` | Sensitive | Explicit consent | Until deleted | No |
| `fit_preference` | Personal | Consent (`personalization`) | Until deleted | No — abstracted |
| `sizes_by_category` | Personal | Consent (`personalization`) | Until deleted | No — abstracted |

## gateway.consents

| Field | Class | Basis | Retention | Leaves system |
|---|---|---|---|---|
| All fields | Compliance record | Legal obligation | 7 years past account closure | No |

## gateway.style_preferences / quiz_responses

| Field | Class | Basis | Retention | Leaves system |
|---|---|---|---|---|
| `dna_scores`, `dna_dominant`, `dna_alter_ego`, `dna_wildcard` | Behavioural | Consent (`personalization`) | Life of account | Persona id only, on share cards |
| `answers` | Behavioural | Consent (`personalization`) | Life of account | No |
| `quiz_version`, `submitted_at` | Operational | Consent (`personalization`) | Life of account | No |

## gateway.vault_items / wear_log

| Field | Class | Basis | Retention | Leaves system |
|---|---|---|---|---|
| `asset_id`, `name`, `category`, `colors`, `fabric`, `brand` | Behavioural | Consent (`personalization`) | Life of account | Attributes to model providers, redacted |
| `notes` | User content | Consent (`personalization`) | Life of account | Redacted before any model call |
| `item_ids`, `occasion`, `worn_on` | Behavioural | Consent (`personalization`) | Life of account | No |

## gateway.saved_looks / feedback_signals / action_events

| Field | Class | Basis | Retention | Leaves system |
|---|---|---|---|---|
| `look_id`, `snapshot` | Behavioural | Consent (`personalization`) | Life of account | No |
| `signal`, `target_id` | Behavioural | Consent (`personalization`) | Life of account | Pseudonymous, to analytics |
| `action`, `surface` | Behavioural | Consent (`analytics`) | 24 months | Pseudonymous, to analytics |

## gateway.integration_accounts

| Field | Class | Basis | Retention | Leaves system |
|---|---|---|---|---|
| `access_token_enc`, `refresh_token_enc` | Credential | Consent (`pinterest_sync`) | Until disconnected | Yes — to Pinterest, for API calls |
| `provider_uid`, `scopes`, `sync_cursor` | Operational | Consent (`pinterest_sync`) | Until disconnected | No |

## gateway.notify_*

| Field | Class | Basis | Retention | Leaves system |
|---|---|---|---|---|
| `token_enc` (device) | Identifier | Contract | Until logout or deletion | Yes — FCM / APNs |
| `preferences` | Preference | Contract | Life of account | No |
| `deliveries` | Operational | Legitimate interest | 12 months | No |
| `inbox` | User-facing content | Contract | 6 months | No |

## gateway.contact_messages

Website enquiries from the contact and partners forms. Not tied to an account.

| Field | Class | Basis | Retention | Leaves system |
|---|---|---|---|---|
| `name_enc`, `email_enc`, `message_enc`, `organisation_enc`, `role_enc` | Identifier and free text | Legitimate interest (answering a request the person made); a data request is also a legal obligation | **72 hours** from receipt | Yes — emailed to the FAUE team's mailbox (`hello@` or `partners@faueofficial.com`) |
| `email_bidx`, `ip_bidx` | Blind index, keyed hash | Legitimate interest (finding one person's messages for export or erasure; abuse control) | **72 hours** | No |
| `reference`, `topic`, `partner_type`, `status`, dates, `policy_version`, `reference_code` | Operational | Legitimate interest | Kept; contains nothing that identifies the sender | No |

Cleared by the `contact_purge` worker (every 15 minutes). The copy in the team's mailbox is outside this database; anything that must outlive 72 hours lives there or in the privacy-request flow, and a data request is tracked against its own 30-day deadline.

## gateway.waitlist_entries

People who took the Style DNA quiz on the website and asked to be told when FAUE opens.

| Field | Class | Basis | Retention | Leaves system |
|---|---|---|---|---|
| `email_enc` | Identifier | Consent (ticked on the form, `policy_version` stored with `consented_at`) | Until FAUE opens and the person has been told, or until they unsubscribe or ask for deletion | Yes: the email provider (Resend) receives it to send the confirmation and the launch email |
| `username`, `username_key` | Identifier (a reservation, not an account) | Consent | As above | No |
| `gender` (`female` or `male`, from a dropdown) | Personal data | Consent | As above | No. Used only to choose the model photograph behind the person's card |
| `dna_answers`, `dna_scores`, `dna_dominant`, `dna_alter_ego`, `dna_wildcard` | Preference data | Consent | As above | No |
| `email_bidx`, `ip_bidx` | Blind index, keyed hash | Legitimate interest (de-duplication, abuse control) | As above | No |
| `status`, `source`, dates, `user_id` | Operational | Consent | As above | No |

Linked to an account when the same email address signs up. Staff reads are audited (`waitlist.viewed`), and a message to one member is audited without its text (`waitlist.messaged`).

## gateway.admin_users / audit_log

| Field | Class | Basis | Retention | Leaves system |
|---|---|---|---|---|
| `email_enc`, `role` | Staff identifier | Contract | Life of employment | No |
| `actor_id`, `action`, `target_id`, `before`, `after`, `ip` | Compliance record | Legal obligation | **7 years** | No |

The audit log survives user deletion. It is the artefact that demonstrates access accountability to a regulator, and deleting it would defeat its purpose.

---

## ase.user_style_context

| Field | Class | Basis | Retention | Leaves system |
|---|---|---|---|---|
| `dna_vector`, `aspiration_vector`, `behavior_vector` | Derived personal data | Consent (`personalization`) | Life of account | No |
| `constraints` | Abstracted sensitive | Consent (`personalization`) | Life of account | Yes — abstract rules only, to model providers |

## ase.*_embeddings

| Field | Class | Basis | Retention | Leaves system |
|---|---|---|---|---|
| `embedding` | Derived personal data | Consent (`personalization`) | Life of the source object | No |
| `attributes` | Derived | Consent (`personalization`) | Life of the source object | Yes — to model providers as pool data |

Embeddings are personal data and are deleted on erasure.

## ase.looks / look_jobs / look_impressions

| Field | Class | Basis | Retention | Leaves system |
|---|---|---|---|---|
| `items`, `description`, `why_this_works` | Generated content | Consent (`ai_processing`) | Life of account; unsaved pruned at 90 days | Yes — on share pages, if shared |
| `image_url` | Generated content | Consent (`ai_processing`) | As above | Yes — on share pages, if shared |
| `position`, `candidate_set_hash` | Operational | Legitimate interest | 12 months | No |

## ase.fabric_analyses

| Field | Class | Basis | Retention | Leaves system |
|---|---|---|---|---|
| `detected_type`, `attributes`, `confidence` | Derived | Consent (`ai_processing`) | Life of account | No |
| `reasoning_by_style` | Generated content | Consent (`ai_processing`) | Life of account | No |

## ase.spree_sessions / spree_messages

| Field | Class | Basis | Retention | Leaves system |
|---|---|---|---|---|
| `content_redacted` | User content, redacted | Consent (`ai_processing`) | **90 days** | Redacted form to model providers |
| `tool_calls`, `guardrail_verdict` | Operational | Legitimate interest | 90 days | No |
| `asset_ids` | Reference | Consent (`camera_photos`) | 90 days | Derivatives to model providers |

Stored already redacted, so a database dump contains no PII.

## ase.agent_memory / agent_runs

| Field | Class | Basis | Retention | Leaves system |
|---|---|---|---|---|
| `value` (profile tier) | Derived personal data | Consent (`personalization`) | Life of account | No |
| `value` (semantic tier) | Derived | Consent (`personalization`) | Decayed continuously | No |
| `value` (episodic tier) | Behavioural | Consent (`personalization`) | 90 days rolling | No |
| `rationale`, `outcome` | Operational | Consent (`agent_proactive`) | 12 months | No |

## ase.weather_cache / model_calls

| Field | Class | Basis | Retention | Leaves system |
|---|---|---|---|---|
| `geohash5`, `payload` | Coarse location | Consent (`location_weather`) | 48 hours | Geohash to weather provider, no identifier |
| `task`, `model_id`, `tokens`, `cost`, `latency` | Operational | Legitimate interest | 90 days | No |
| `trace_id` | Operational | Legitimate interest | 90 days | No |

---

## media.assets

| Field | Class | Basis | Retention | Leaves system |
|---|---|---|---|---|
| `cdn_url` (derivative) | Image, redacted | Consent (`camera_photos`) | Life of the object | Yes — CDN and model providers |
| Original image | Image, unredacted | Explicit consent only | **Discarded by default** | No |
| `exif_stripped`, `faces_redacted`, `ocr_redacted`, `safety_verdict` | Compliance record | Legal obligation | Life of the object | No |

---

## Sub-processors

| Processor | Purpose | Data | Location | DPA |
|---|---|---|---|---|
| OpenRouter → model providers | Language model inference | Redacted text and images | Varies — zero-retention allowlist | Required |
| Image generation provider | Look rendering | Constructed prompts only | TBD at selection | Required |
| Cloudinary | Primary image storage, CDN, transforms | Redacted derivatives | Global CDN | Required |
| Cloudflare R2 | Backup replica of derivatives | Redacted derivatives | Configurable region | Required |
| Resend | Magic links, transactional email | Email address | US/EU | Required |
| FCM / APNs | Push delivery | Device tokens | Global | Standard terms |
| PostHog | Product analytics | Pseudonymous events | EU or self-hosted | Required |
| Open-Meteo | Weather | Coarse geohash, no identifier | EU | Public API |
| Pinterest | Board import | OAuth token, on user request | Global | Platform terms |
| Railway | Hosting | All service data | Selected region | Required |
| Vercel | Static hosting | No user data at rest | Global CDN | Standard terms |

---

## Review checklist

Quarterly, and on any schema change:

1. Does every column in every schema appear here? A column without a row is a finding.
2. Does every field have a lawful basis that still holds?
3. Is every retention period enforced by the `retention_ttl` worker, not merely stated?
4. Has any new third party received data without a DPA?
5. Does the published sub-processor list match this table?
6. Do the consent purposes in code match the purposes named here?
