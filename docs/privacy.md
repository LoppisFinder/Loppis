# LoppisFinder privacy and GDPR design

## Principles

1. **No real identity** — no names, emails, phone numbers, or OAuth profiles.
2. **Anonymous sessions** — server-generated UUID + JWT only.
3. **PII stripping** — all crawled and user-submitted text sanitized before storage.
4. **Hashed tokens** — push notification tokens stored as SHA-256 hashes only.
5. **Data minimization** — only data required for loppis discovery and alerts.

## Retention

| Data | Retention |
|---|---|
| Past loppis events | 90 days after end date |
| Inactive anonymous sessions | 12 months since last activity |
| Rate-limit Redis keys | 24 hours |
| Crawled source snippets | Until event purged |

## User rights

- **Export**: `GET /v1/me/export` — favorites, alerts, preferences
- **Erasure**: `DELETE /v1/me` — hard delete all user-linked data

## Crawler PII rules

Strip before persistence:
- Email addresses → `[email]`
- Phone numbers → `[telefon]`
- Social handles → `[användare]`
- Profile URLs → `[profil]`

Forum authors stored as one-way `author_hash` for deduplication only.
