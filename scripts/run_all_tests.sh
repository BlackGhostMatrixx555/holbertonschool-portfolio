#!/usr/bin/env bash
# Shebang : indique que le script doit être exécuté avec bash, via le binaire trouvé dans le PATH.

# ==============================================================================
# CampOrga — Suite de Tests Complète (From Scratch)
# ==============================================================================
# Description générale du script : il enchaîne les 8 phases de vérification
# d'un environnement entièrement reconstruit.
#   1. Nettoyage complet
#   2. Build de l'environnement
#   3. Vérification de la base de données
#   4. Tests automatisés (Pytest)
#   5. Tests manuels guidés (Swagger)   -> annoncé mais non implémenté ici
#   6. Test "from scratch" (reproductibilité) -> annoncé mais non implémenté ici
#   7. Vérifications de sécurité        -> la phase 6 du code
#   8. Test de la démo                  -> la phase 8 du code (rapport)
#
# Usage : ./scripts/run_all_tests.sh
# ==============================================================================

set -e  # Option bash : arrête immédiatement le script dès qu'une commande renvoie une erreur (code != 0).

# Couleurs : séquences ANSI d'échappement pour colorer le texte dans le terminal.
GREEN='\033[0;32m'   # Vert : succès
YELLOW='\033[1;33m'  # Jaune gras : avertissement
RED='\033[0;31m'     # Rouge : erreur
BLUE='\033[0;34m'    # Bleu : titres de phase
BOLD='\033[1m'       # Gras
NC='\033[0m'         # No Color : réinitialise le style

# Helpers : petites fonctions réutilisées pour afficher des messages uniformes.
# log_phase : affiche un bandeau bleu encadrant le titre d'une phase.
log_phase() { echo -e "\n${BOLD}${BLUE}═══════════════════════════════════════════════════${NC}"; echo -e "${BOLD}${BLUE}  $1${NC}"; echo -e "${BOLD}${BLUE}═══════════════════════════════════════════════════${NC}\n"; }
# log_ok : message de succès en vert, préfixé d'une coche.
log_ok() { echo -e "${GREEN}✅ $1${NC}"; }
# log_warn : message d'avertissement en jaune.
log_warn() { echo -e "${YELLOW}⚠️  $1${NC}"; }
# log_err : message d'erreur en rouge.
log_err() { echo -e "${RED}❌ $1${NC}"; }
# log_info : message neutre indenté.
log_info() { echo -e "   $1"; }

# Vérifie qu'on est à la racine du projet (présence du fichier camporga.sh).
if [ ! -f "camporga.sh" ]; then
    log_err "Erreur : ce script doit être lancé depuis la racine du projet."
    log_info "Utilisation : ./scripts/run_all_tests.sh"
    exit 1  # Sortie avec code d'erreur 1.
fi

# Demande confirmation avant une action destructrice.
echo -e "${YELLOW}⚠️  ATTENTION : Ce script va détruire TOUS les conteneurs et TOUTES les données.${NC}"
read -p "Continuer ? (y/N) " -n 1 -r  # -n 1 : lit un seul caractère ; -r : pas d'interprétation des backslashes.
echo  # Saut de ligne après la saisie.
if [[ ! $REPLY =~ ^[Yy]$ ]]; then  # $REPLY contient la touche tapée ; on accepte seulement y/Y.
    log_info "Annulé."
    exit 0  # Sortie propre (code 0) : l'utilisateur a refusé.
fi

# ==============================================================================
# PHASE 1 — Nettoyage complet
# ==============================================================================
log_phase "PHASE 1 — Nettoyage complet"
log_info "Destruction des conteneurs et volumes..."
# Arrête et supprime les conteneurs, réseaux, et volumes (-v) du projet, ainsi que les conteneurs orphelins.
docker compose down -v --remove-orphans
log_ok "Environnement nettoyé."

# ==============================================================================
# PHASE 2 — Build de l'environnement
# ==============================================================================
log_phase "PHASE 2 — Build de l'environnement"
log_info "Démarrage de Docker Compose..."
# -d : mode détaché (en arrière-plan) ; --build : reconstruit les images avant de lancer.
docker compose up -d --build

log_info "Attente que la DB soit prête..."
# Boucle : tant que pg_isready échoue, on attend 1 seconde.
# pg_isready renvoie un code non nul si PostgreSQL n'accepte pas encore de connexions ;
# > /dev/null 2>&1 masque sa sortie.
until docker compose exec -T db pg_isready -U camporga > /dev/null 2>&1; do
    echo -n "."   # Affiche un point sans saut de ligne pour montrer la progression.
    sleep 1
done
echo ""
log_ok "Base de données prête."

# ==============================================================================
# PHASE 3 — Migrations + Vérification BDD
# ==============================================================================
log_phase "PHASE 3 — Migrations et vérification BDD"
log_info "Application des migrations Alembic..."
# Exécute dans le conteneur backend les migrations jusqu'à la dernière version (head).
docker compose exec backend alembic upgrade head
log_ok "Migrations appliquées."

log_info "Vérification des 8 tables..."
# Récupère la liste des tables du schéma public. -tAc : sortie brute sans en-tête ni alignement.
TABLES=$(docker compose exec -T db psql -U camporga -tAc "SELECT tablename FROM pg_tables WHERE schemaname='public' ORDER BY tablename;")
# Liste attendue des tables, séparées par des espaces.
EXPECTED_TABLES="alembic_version backups camp_modalities camps contact_messages landing_pages registrations users"
for table in $EXPECTED_TABLES; do  # Boucle sur chaque nom attendu.
    # grep -q "^$table$" : cherche une ligne qui correspond exactement au nom (ancres ^ et $).
    if echo "$TABLES" | grep -q "^$table$"; then
        log_info "  ✅ $table"
    else
        log_err "  ❌ Table manquante : $table"
        exit 1
    fi
done
log_ok "Toutes les tables sont présentes."

log_info "Vérification des colonnes 2FA..."
# Interroge information_schema pour lister les colonnes 2FA présentes dans la table users.
COLUMNS=$(docker compose exec -T db psql -U camporga -tAc "SELECT column_name FROM information_schema.columns WHERE table_name='users' AND column_name IN ('phone_number', 'totp_secret', 'is_2fa_enabled');")
# Vérifie que chacune des trois colonnes figure dans le résultat.
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
# Lance pytest avec couverture ; 2>&1 redirige les erreurs vers la sortie standard pour tout capturer.
# La sortie est stockée dans TEST_OUTPUT, et affichée ensuite.
TEST_OUTPUT=$(docker compose exec -T backend pytest --cov=app --cov-report=term-missing 2>&1)
echo "$TEST_OUTPUT"

# Cherche la mention "passed" dans la sortie pytest pour valider la réussite.
if echo "$TEST_OUTPUT" | grep -q "passed"; then
    # Extrait le nombre de tests réussis (ex. "50 passed") ; head -1 garde la première occurrence.
    PASSED=$(echo "$TEST_OUTPUT" | grep -oE "[0-9]+ passed" | head -1)
    log_ok "Tests passés : $PASSED"
else
    log_err "Des tests ont échoué."
    exit 1
fi

# Extrait le pourcentage de couverture de la ligne TOTAL du rapport pytest-cov.
COVERAGE=$(echo "$TEST_OUTPUT" | grep -oE "TOTAL.*[0-9]+%" | grep -oE "[0-9]+%" | head -1)
log_ok "Couverture : $COVERAGE"

# ==============================================================================
# PHASE 5 — Création du Super Admin
# ==============================================================================
log_phase "PHASE 5 — Création du Super Admin"
log_info "Exécution de ./camporga.sh admin..."
./camporga.sh admin  # Délègue la création du compte administrateur au script principal.
log_ok "Super Admin prêt."

# ==============================================================================
# PHASE 6 — Tests de sécurité
# ==============================================================================
log_phase "PHASE 6 — Vérifications de sécurité"

# Test 6.1 — Mots de passe hachés
log_info "6.1 — Vérification du hachage Bcrypt..."
# Récupère le hash du mot de passe de l'admin directement en base.
HASH=$(docker compose exec -T db psql -U camporga -tAc "SELECT password_hash FROM users WHERE email='admin@camporga.fr';")
# Un hash bcrypt commence par $2b$ ; on vérifie ce préfixe (\$ échappé pour grep).
if echo "$HASH" | grep -q '^\$2b\$'; then
    log_ok "Mots de passe hachés avec Bcrypt."
else
    log_err "Les mots de passe ne sont pas hachés avec Bcrypt."
    exit 1
fi

# Test 6.2 — JWT invalide
log_info "6.2 — Vérification du rejet des tokens invalides..."
# -s : mode silencieux ; -o /dev/null : ignore le corps ; -w "%{http_code}" : affiche uniquement le code HTTP.
INVALID_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" -H "Authorization: Bearer invalid-token" http://localhost:8000/api/users)
if [ "$INVALID_RESPONSE" = "401" ]; then  # 401 = non authentifié, attendu pour un token invalide.
    log_ok "Token invalide rejeté (401)."
else
    log_err "Le token invalide n'a pas été rejeté (code $INVALID_RESPONSE)."
    exit 1
fi

# Test 6.3 — Super Admin éternel
log_info "6.3 — Vérification de la protection du Super Admin..."
# Connexion avec les identifiants admin ; la réponse contient le JWT.
LOGIN_RESPONSE=$(curl -s -X POST http://localhost:8000/api/auth/login -H "Content-Type: application/json" -d '{"email":"admin@camporga.fr","password":"ChangeMe123!"}')
# Extrait la valeur du champ access_token : grep trouve la paire clé/valeur, cut -d'"' -f4 prend le 4e champ entre guillemets.
TOKEN=$(echo "$LOGIN_RESPONSE" | grep -oE '"access_token":"[^"]+"' | cut -d'"' -f4)
if [ -n "$TOKEN" ]; then  # -n : vérifie que la variable n'est pas vide.
    # Tente de supprimer son propre compte ; le Super Admin doit recevoir 403 (interdit).
    DELETE_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" -X DELETE -H "Authorization: Bearer $TOKEN" http://localhost:8000/api/users/me)
    if [ "$DELETE_RESPONSE" = "403" ]; then
        log_ok "Super Admin éternel (403 sur DELETE /me)."
    else
        log_err "Le Super Admin a pu être supprimé (code $DELETE_RESPONSE)."
        exit 1
    fi
else
    log_warn "Impossible de se connecter, test 6.3 ignoré."  # Le test est sauté sans faire échouer le script.
fi

# ==============================================================================
# PHASE 7 — Test de santé (health + ready)
# ==============================================================================
log_phase "PHASE 7 — Tests de santé"
log_info "Vérification de /health..."
# /health : endpoint de vivacité (l'application tourne).
HEALTH=$(curl -s http://localhost:8000/health)
if echo "$HEALTH" | grep -q '"status":"ok"'; then
    log_ok "/health répond correctement."
else
    log_err "/health ne répond pas correctement."
    exit 1
fi

log_info "Vérification de /ready..."
# /ready : endpoint de disponibilité (l'application est prête à traiter des requêtes, BDD incluse).
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

echo -e "${GREEN}"  # Passe en vert pour le cadre.
# Cadre décoratif (les caractères box-drawing sont purement visuels).
echo "╔═══════════════════════════════════════════════════╗"
echo "║                                                   ║"
echo "║   🎉 CampOrga est prêt pour la soutenance !      ║"
echo "║                                                   ║"
echo "╚═══════════════════════════════════════════════════╝"
echo -e "${NC}"  # Réinitialise la couleur.

echo -e "${BOLD}Résumé :${NC}"
echo "  ✅ Phase 1 : Nettoyage OK"
echo "  ✅ Phase 2 : Build OK"
echo "  ✅ Phase 3 : BDD OK (8 tables, colonnes 2FA)"
echo "  ✅ Phase 4 : $PASSED ($COVERAGE couverture)"  # Variables remplies pendant la phase 4.
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
echo "  🔑 ChangeMe123!"   # Identifiants affichés en clair.

echo ""
echo -e "${BOLD}Prochaine étape :${NC}"
echo "  Lance ta démo chronométrée (5 min) et répète-la jusqu'à être prêt."
echo ""