# 📚 Documentation — CampOrga

🇫🇷 Français | 🇬🇧 [English](./README.en.md)

Ce dossier regroupe toute la documentation du projet. Pour l'installation et la vue d'ensemble, voir le [README principal](../README.md).

## Données

| Fichier | Contenu |
|---|---|
| [`database-schema.sql`](./database-schema.sql) | Schéma PostgreSQL lisible (7 tables, enums) et description des collections MongoDB — à jour avec la migration `e7a1c3f90b21` |
| [`diagram_database.png`](./diagram_database.png) | Diagramme entité-association (PostgreSQL + MongoDB) |
| [`diagram_database.mmd`](./diagram_database.mmd) | Source Mermaid du diagramme (`mmdc -i diagram_database.mmd -o diagram_database.png -t dark -b black`) |
| [`database-schema.pdf`](./database-schema.pdf) | Version PDF du diagramme |

**Répartition des données**

- **PostgreSQL** : `users`, `camps`, `camp_modalities`, `landing_pages`, `registrations`, `contact_messages`, `backups` — données métier, intégrité relationnelle.
- **MongoDB** : `chat_conversations` (une conversation du chatbot par session, supprimée après 90 jours d'inactivité) et `verification_codes` (code email/SMS haché, expiré après 5 minutes) — documents imbriqués et données temporaires avec index TTL.

## Projet

| Fichier | Contenu |
|---|---|
| [`project-presentation.md`](./project-presentation.md) | Présentation complète : architecture, API, sécurité, tests, infrastructure |
| [`CHANGELOG.md`](./CHANGELOG.md) | Historique des versions (2.0.0 = fusion `collins` + `tete-work`) |
| [`scalability-roadmap.md`](./scalability-roadmap.md) | Évolution de l'architecture de 10 à 100 000 utilisateurs |
| [`SOD20_Scalabilite_10_a_100000.pdf`](./SOD20_Scalabilite_10_a_100000.pdf) | Support de présentation sur la scalabilité |
| [`commandes_a_entrer.txt`](./commandes_a_entrer.txt) | Aide-mémoire des commandes terminal |

## Livrables Holberton (datés, non modifiés)

| Fichier | Étape |
|---|---|
| [`stage1-report-en.pdf`](./stage1-report-en.pdf) | Étape 1 — Idée et formation de l'équipe |
| [`stage2-project-planning-en.pdf`](./stage2-project-planning-en.pdf) | Étape 2 — Planification du projet |
| [`stage3-technical-documentation.pdf`](./stage3-technical-documentation.pdf) | Étape 3 — Documentation technique |
| [`cahier-des-charges.pdf`](./cahier-des-charges.pdf) | Cahier des charges |
| [`use-cases.pdf`](./use-cases.pdf) | Cas d'utilisation |

## Prototypes et outils

| Fichier | Contenu |
|---|---|
| [`summer-camp-prototype.html`](./summer-camp-prototype.html) | Premier prototype statique de landing page |
| [`2fa-tester.html`](./2fa-tester.html) | Page de test manuel de la double authentification |
| [`screenshots/`](./screenshots/) | Captures (dont une conversation du chatbot stockée dans MongoDB) |
