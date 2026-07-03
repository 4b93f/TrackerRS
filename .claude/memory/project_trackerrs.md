---
name: TrackerRS project context
description: Discord bot that tracks Instagram accounts and notifies Discord channels on new posts
type: project
---

Building a Discord bot (TrackerRS) that tracks Instagram accounts and sends Discord notifications on new posts.

**Flow:** Instagram creator OAuth → Meta webhook on new post → server processes → Discord webhook notification

**Stack:**
- Instagram Graph API (webhooks + media endpoints)
- Neon (serverless Postgres) — store OAuth tokens + seen post IDs
- Discord webhook
- Backend: Node.js or Python (TBD)

**Constraints:**
- Only tracks accounts that explicitly authorized via OAuth
- Free tier only
- Meta app in development mode (max 25 test users)

**Why:** Need real OAuth flow because webhooks only fire for authorized accounts.
**How to apply:** All architecture decisions should optimize for free tier, simplicity, and Meta's webhook model.
