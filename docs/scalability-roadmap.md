# CampOrga — Roadmap de Scalabilité (De 10 à 100 000 utilisateurs)

Ce document décrit comment l'architecture de CampOrga évoluerait pour passer d'un MVP local (10 utilisateurs) à une plateforme à grande échelle (100 000 utilisateurs). Il s'appuie sur la présentation "De 10 à 100 000 utilisateurs" (SOD nº20).

## 📊 État actuel (MVP — 10 utilisateurs)

L'architecture actuelle est **monolithique et conteneurisée** :
- **Frontend** : React (Vite) servi par un serveur statique.
- **Backend** : 1 conteneur FastAPI (Uvicorn).
- **Base de données** : 1 conteneur PostgreSQL 16.
- **Déploiement** : Docker Compose sur une seule machine (local ou VPS).

**Limites identifiées** :
- **Point de défaillance unique (SPOF)** : si le conteneur backend ou la base tombe, tout s'arrête.
- **Sessions en mémoire** : les JWT sont stateless (bon point), mais les backups sont stockés sur le disque local.
- **Déploiement manuel** : `docker compose up -d` (pas de CI/CD automatisé).

---

## 🚀 Étape 1 : De 10 à 1 000 utilisateurs (Maintenant)

**Objectif** : Rendre le backend robuste et automatisé sans changer l'architecture globale.

### Actions à mettre en place :
1. **Backend Stateless** :
   - Le JWT est déjà utilisé (pas de session en mémoire). ✅
   - Les fichiers de backup doivent être sortis du disque local (voir Étape 2).
2. **Index et requêtes saines** :
   - Ajouter des index sur les colonnes fréquemment recherchées (ex: `registrations.email`, `camps.slug` déjà en UNIQUE). ✅
   - Utiliser `EXPLAIN ANALYZE` pour vérifier les requêtes lentes.
3. **CI/CD** :
   - Mettre en place **GitHub Actions** pour lancer `pytest` et `ruff` à chaque push.
   - Automatiser les migrations Alembic (`alembic upgrade head`).
4. **Sauvegardes** :
   - Automatiser `pg_dump` (cron job ou service dédié) au lieu de le déclencher manuellement.
   - Stocker les backups sur un volume persistant (pas dans le conteneur).

---

## 📈 Étape 2 : De 1 000 à 10 000 utilisateurs (Ensuite)

**Objectif** : Supporter la charge sans dégrader les temps de réponse.

### Actions à mettre en place :
1. **Cache & Sessions (Redis)** :
   - Ajouter **Redis** pour mettre en cache les requêtes lourdes (ex: `GET /api/camps` qui liste tous les camps).
   - Utiliser `Cache-Aside` : le backend vérifie Redis, sinon interroge Postgres et met en cache.
   - Remplacer le stockage local des backups par un **Object Storage** (S3, MinIO).
2. **Object Storage + CDN** :
   - Déplacer les backups, les images de landing page et les fichiers statiques vers **S3 / MinIO**.
   - Ajouter un **CDN** (Cloudflare) devant le frontend React pour servir les assets.
3. **Load Balancer + Réplicas** :
   - Déployer plusieurs instances du backend derrière un **Load Balancer** (Nginx, Traefik, ou ALB).
   - Ajouter des **réplicas en lecture** pour PostgreSQL (ex: 1 primary + 2 replicas).
   - Le backend doit être capable de router les lectures vers les replicas et les écritures vers le primary (via SQLAlchemy ou un middleware).

---

## 🏗️ Étape 3 : Vers 100 000 utilisateurs (À 100k+)

**Objectif** : Passage à l'échelle horizontale et tolérance aux pannes.

### Actions à mettre en place :
1. **Autoscaling** :
   - Utiliser **Kubernetes** (ou AWS ECS) pour orchestrer les conteneurs.
   - Configurer le **Horizontal Pod Autoscaler (HPA)** pour ajouter des instances backend selon l'usage CPU/RAM.
2. **Files et Workers** :
   - Sortir les tâches lourdes (génération de backup, envoi d'emails) du backend synchrone.
   - Utiliser une file de messages (**RabbitMQ** ou **Redis Queue**) avec des workers (Celery) pour les traiter en arrière-plan.
3. **Monitoring** :
   - Ajouter **Prometheus + Grafana** pour surveiller les métriques (latence, taux d'erreur, connexions DB).
   - Configurer des alertes en cas de saturation.
4. **Sharding (si nécessaire)** :
   - Si la base de données devient trop grosse, partitionner la table `camps` par année ou par région.
   - Utiliser **pg_partman** pour Postgres.

---

## 💡 Résumé des évolutions

| Palier | Infrastructure | Base de données | Fichiers | Déploiement |
|---|---|---|---|---|
| **10** | 1 instance Docker | PostgreSQL | Disque local | Manuel |
| **1k** | CI/CD, Load Balancer | + Réplicas lecture | Object Storage | Automatisé |
| **10k** | + Redis Cache | Pool (PgBouncer) | CDN | Rolling update |
| **100k** | Kubernetes (Auto-scaling) | Partitionnement | File de messages | Blue/Green |

---

## 🎯 Pourquoi ce document ?

Ce plan de scalabilité montre que l'architecture actuelle a été pensée pour évoluer. Même si le MVP (Stage 4) est déployé sur une seule machine avec Docker Compose, le code et le schéma de base de données sont déjà compatibles avec les étapes futures (stateless backend, JWT, index).
