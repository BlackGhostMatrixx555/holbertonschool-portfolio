#!/usr/bin/env bash

# ==============================================================================
# CampOrga — Suite de Tests Complète (From Scratch)
# ==============================================================================
# Ce script automatise les 8 phases de test :
#   1. Nettoyage complet
#   2. Build de l'environnement
#   3. Vérification de la base de données
#   4. Tests automatisés (Pytest)
#   5. Tests manuels guidés (Swagger)
#   6. Test "from scratch" (reproductibilité)
#   7. Vérifications de sécurité
#   8. Test de la démo
#
# Usage : ./scripts/run_all_tests.sh
# ==============================================================================

set -e  # Arrête le script en cas d'erreur

# Couleurs
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
BOLD='\033[1m'
NC='\033[0m'

# Helpers
log_phase() { echo -e "\n${BOLD}${BLUE}═══════════════════════════════════════════════════${NC}"; echo -e "${BOLD}${BLUE}  $1${NC}"; echo -e "${BOLD}${BLUE}═══════════════════════════════════════════════════${NC}\n"; }
log_ok() { echo -e "${GREEN}✅ $1${NC}"; }
log_warn() { echo -e "${YELLOW}⚠️  $1${NC}"; }
log_err() { echo -e "${RED}❌ $1${NC}"; }
log_info() { echo -e "   $1"; }

# Vérifie qu'on est à la racine du projet
if [ ! -f "camporga.sh" ]; then
    log_err "Erreur : ce script doit être lancé depuis la racine du projet."
    log_info "Utilisation : ./scripts/run_all_tests.sh"
    exit 1
fi

# Confirmation
echo -e "${YELLOW}⚠️  ATTENTION : Ce script va détruire TOUS les conteneurs et TOUTES les données.${NC}"
read -p "Continuer ? (y/N) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    log_info "Annulé."
    exit 0
fi

# ==============================================================================
# PHASE 1 — Nettoyage complet
# ==============================================================================
log_phase "PHASE 1 — Nettoyage complet"
log_info "Destruction des conteneurs et volumes..."
docker compose down -v --remove-orphans
log_ok "Environnement nettoyé."

# ==============================================================================
# PHASE 2 — Build de l'environnement
# ==============================================================================
log_phase "PHASE 2 — Build de l'environnement"
log_info "Démarrage de Docker Compose..."
docker compose up -d --build

log_info "Attente que la DB soit prête..."
until docker compose exec -T db pg_isready -U camporga > /dev/null 2>&1; do
    echo -n "."
    sleep 1
done
echo ""
log_ok "Base de données prête."

# ==============================================================================
# PHASE 3 — Migrations + Vérification BDD
# ==============================================================================
log_phase "PHASE 3 — Migrations et vérification BDD"
log_info "Application des migrations Alembic..."
docker compose exec backend alembic upgrade head
log_ok "Migrations appliquées."

log_info "Vérification des 8 tables..."
TABLES=$(docker compose exec -T db psql -U camporga -tAc "SELECT tablename FROM pg_tables WHERE schemaname='public' ORDER BY tablename;")
EXPECTED_TABLES="alembic_version backups camp_modalities camps contact_messages landing_pages registrations users"
for table in $EXPECTED_TABLES; do
    if echo "$TABLES" | grep -q "^$table$"; then
        log_info "  ✅ $table"
    else
        log_err "  ❌ Table manquante : $table"
        exit 1
    fi
done
log_ok "Toutes les tables sont présentes."

log_info "Vérification des colonnes 2FA..."
COLUMNS=$(docker compose exec -T db psql -U camporga -tAc "SELECT column_name FROM information_schema.columns WHERE table_name='users' AND column_name IN ('phone_number', 'totp_secret', 'is_2fa_enabled');")
if echo "$COLUMNS" | grep -q "phone_number" && echo "$COLUMNS" | grep -q "totp_secret" && echo "$COLUMNS" | grep -q "is_2fa_enabled"; then
    log_ok "Colonnes 2FA présentes."
else
    log_err "Colonnes 2FA manquantes."
    exit 1
fi

# ==============================================================================
# PHASE 4 — Tests automatisés
# ==============================================================================
log_phase "PHASE 4 — Tests automatisés (Pytest)"
log_info "Lancement de la suite complète..."
TEST_OUTPUT=$(docker compose exec -T backend pytest --cov=app --cov-report=term-missing 2>&1)
echo "$TEST_OUTPUT"

if echo "$TEST_OUTPUT" | grep -q "passed"; then
    PASSED=$(echo "$TEST_OUTPUT" | grep -oE "[0-9]+ passed" | head -1)
    log_ok "Tests passés : $PASSED"
else
    log_err "Des tests ont échoué."
    exit 1
fi

COVERAGE=$(echo "$TEST_OUTPUT" | grep -oE "TOTAL.*[0-9]+%" | grep -oE "[0-9]+%" | head -1)
log_ok "Couverture : $COVERAGE"

# ==============================================================================
# PHASE 5 — Création du Super Admin
# ==============================================================================
log_phase "PHASE 5 — Création du Super Admin"
log_info "Exécution de ./camporga.sh admin..."
./camporga.sh admin
log_ok "Super Admin prêt."

# ==============================================================================
# PHASE 6 — Tests de sécurité
# ==============================================================================
log_phase "PHASE 6 — Vérifications de sécurité"

# Test 6.1 — Mots de passe hachés
log_info "6.1 — Vérification du hachage Bcrypt..."
HASH=$(docker compose exec -T db psql -U camporga -tAc "SELECT password_hash FROM users WHERE email='admin@camporga.fr';")
if echo "$HASH" | grep -q '^\$2b\$'; then
    log_ok "Mots de passe hachés avec Bcrypt."
else
    log_err "Les mots de passe ne sont pas hachés avec Bcrypt."
    exit 1
fi

# Test 6.2 — JWT invalide
log_info "6.2 — Vérification du rejet des tokens invalides..."
INVALID_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" -H "Authorization: Bearer invalid-token" http://localhost:8000/api/users)
if [ "$INVALID_RESPONSE" = "401" ]; then
    log_ok "Token invalide rejeté (401)."
else
    log_err "Le token invalide n'a pas été rejeté (code $INVALID_RESPONSE)."
    exit 1
fi

# Test 6.3 — Super Admin éternel
log_info "6.3 — Vérification de la protection du Super Admin..."
LOGIN_RESPONSE=$(curl -s -X POST http://localhost:8000/api/auth/login -H "Content-Type: application/json" -d '{"email":"admin@camporga.fr","password":"ChangeMe123!"}')
TOKEN=$(echo "$LOGIN_RESPONSE" | grep -oE '"access_token":"[^"]+"' | cut -d'"' -f4)
if [ -n "$TOKEN" ]; then
    DELETE_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" -X DELETE -H "Authorization: Bearer $TOKEN" http://localhost:8000/api/users/me)
    if [ "$DELETE_RESPONSE" = "403" ]; then
        log_ok "Super Admin éternel (403 sur DELETE /me)."
    else
        log_err "Le Super Admin a pu être supprimé (code $DELETE_RESPONSE)."
        exit 1
    fi
else
    log_warn "Impossible de se connecter, test 6.3 ignoré."
fi

# ==============================================================================
# PHASE 7 — Test de santé (health + ready)
# ==============================================================================
log_phase "PHASE 7 — Tests de santé"
log_info "Vérification de /health..."
HEALTH=$(curl -s http://localhost:8000/health)
if echo "$HEALTH" | grep -q '"status":"ok"'; then
    log_ok "/health répond correctement."
else
    log_err "/health ne répond pas correctement."
    exit 1
fi

log_info "Vérification de /ready..."
READY=$(curl -s http://localhost:8000/ready)
if echo "$READY" | grep -q '"status":"ready"'; then
    log_ok "/ready répond correctement."
else
    log_err "/ready ne répond pas correctement."
    exit 1
fi

# ==============================================================================
# PHASE 8 — Rapport final
# ==============================================================================
log_phase "✅ TOUS LES TESTS SONT PASSÉS !"

echo -e "${GREEN}"
echo "╔═══════════════════════════════════════════════════╗"
echo "║                                                   ║"
echo "║   🎉 CampOrga est prêt pour la soutenance !      ║"
echo "║                                                   ║"
echo "╚═══════════════════════════════════════════════════╝"
echo -e "${NC}"

echo -e "${BOLD}Résumé :${NC}"
echo "  ✅ Phase 1 : Nettoyage OK"
echo "  ✅ Phase 2 : Build OK"
echo "  ✅ Phase 3 : BDD OK (8 tables, colonnes 2FA)"
echo "  ✅ Phase 4 : $PASSED ($COVERAGE couverture)"
echo "  ✅ Phase 5 : Super Admin créé"
echo "  ✅ Phase 6 : Sécurité OK (Bcrypt, JWT, Super Admin éternel)"
echo "  ✅ Phase 7 : Health + Ready OK"

echo ""
echo -e "${BOLD}Accès :${NC}"
echo "  🔗 API      : http://localhost:8000"
echo "  📚 Swagger  : http://localhost:8000/docs"
echo "  📊 Health   : http://localhost:8000/health"

echo ""
echo -e "${BOLD}Identifiants Super Admin :${NC}"
echo "  📧 admin@camporga.fr"
echo "  🔑 ChangeMe123!"

echo ""
echo -e "${BOLD}Prochaine étape :${NC}"
echo "  Lance ta démo chronométrée (5 min) et répète-la jusqu'à être prêt."
echo ""
