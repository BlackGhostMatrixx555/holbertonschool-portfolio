# 📚 Documentation — CampOrga

🇫🇷 [Français](./README.md) | 🇬🇧 English

This folder holds all the project documentation. For installation and the overview, see the [main README](../README.en.md).

## Data

| File | Content |
|---|---|
| [`database-schema.sql`](./database-schema.sql) | Readable PostgreSQL schema (7 tables, enums) and description of the MongoDB collections — up to date with migration `e7a1c3f90b21` |
| [`diagram_database.png`](./diagram_database.png) | Entity-relationship diagram (PostgreSQL + MongoDB) |
| [`diagram_database.mmd`](./diagram_database.mmd) | Mermaid source of the diagram (`mmdc -i diagram_database.mmd -o diagram_database.png -t dark -b black`) |
| [`database-schema.pdf`](./database-schema.pdf) | PDF version of the diagram |

**How the data is split**

- **PostgreSQL**: `users`, `camps`, `camp_modalities`, `landing_pages`, `registrations`, `contact_messages`, `backups` — business data, relational integrity.
- **MongoDB**: `chat_conversations` (one chatbot conversation per session, deleted after 90 days of inactivity) and `verification_codes` (hashed email/SMS code, expires after 5 minutes) — nested documents and temporary data with TTL indexes.

## Project

| File | Content |
|---|---|
| [`project-presentation.md`](./project-presentation.md) | Full presentation (French): architecture, API, security, tests, infrastructure |
| [`CHANGELOG.md`](./CHANGELOG.md) | Version history (2.0.0 = `collins` + `tete-work` merge) |
| [`scalability-roadmap.md`](./scalability-roadmap.md) | Architecture evolution from 10 to 100,000 users |
| [`SOD20_Scalabilite_10_a_100000.pdf`](./SOD20_Scalabilite_10_a_100000.pdf) | Scalability presentation slides |
| [`commandes_a_entrer.txt`](./commandes_a_entrer.txt) | Terminal command cheat sheet |

## Holberton deliverables (dated, unchanged)

| File | Stage |
|---|---|
| [`stage1-report-en.pdf`](./stage1-report-en.pdf) | Stage 1 — Idea and team formation |
| [`stage2-project-planning-en.pdf`](./stage2-project-planning-en.pdf) | Stage 2 — Project planning |
| [`stage3-technical-documentation.pdf`](./stage3-technical-documentation.pdf) | Stage 3 — Technical documentation |
| [`cahier-des-charges.pdf`](./cahier-des-charges.pdf) | Specifications |
| [`use-cases.pdf`](./use-cases.pdf) | Use cases |

## Prototypes and tools

| File | Content |
|---|---|
| [`summer-camp-prototype.html`](./summer-camp-prototype.html) | First static landing page prototype |
| [`2fa-tester.html`](./2fa-tester.html) | Manual test page for two-factor authentication |
| [`screenshots/`](./screenshots/) | Screenshots (including a chatbot conversation stored in MongoDB) |
