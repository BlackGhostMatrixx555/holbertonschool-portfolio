#!/usr/bin/env bash

# ==============================================================================
# CampOrga — Script de gestion du cycle de vie (Docker/Podman + Frontend)
# ==============================================================================

set -e

# --- Couleurs ---
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1" >&2; }
log_error() { echo -e "${RED}[ERROR]${NC} $1" >&2; }

# --- Port occupé ? (lsof si disponible, sinon ss) ---
port_in_use() {
    if command -v lsof &> /dev/null; then
        lsof -ti:"$1" > /dev/null 2>&1
    else
        ss -ltn "sport = :$1" 2>/dev/null | grep -q LISTEN
    fi
}

usage() {
    echo "Usage: $0 {start|stop|restart|cleanup|test|admin|admin-reset|frontend|frontend-stop|format|logs|ps|doctor}"
    echo ""
    echo "  start          : Démarre PostgreSQL + MongoDB + API (et applique les migrations)"
    echo "  stop           : Arrête PostgreSQL + MongoDB + API (données conservées)"
    echo "  restart        : Redémarre le backend"
    echo "  cleanup        : Détruit tout (conteneurs + volumes : données supprimées)"
    echo "  test           : Lance la suite de tests avec couverture"
    echo "  admin          : Crée le Super Admin (ou affiche celui qui existe)"
    echo "  admin-reset    : Supprime et recrée le Super Admin"
    echo "  frontend       : Démarre le serveur Vite (bloquant, Ctrl+C pour quitter)"
    echo "  frontend-stop  : Arrête le serveur Vite (port 5173)"
    echo "  format         : Formate le code Python"
    echo "  logs           : Affiche les logs du backend"
    echo "  ps             : Affiche l'état des services"
    echo "  doctor         : Diagnostique l'environnement (moteur de conteneurs, ports, .env)"
}

# --- Diagnostic : pourquoi le moteur de conteneurs est-il inutilisable ? ---
diagnose_engine() {
    local found=0
    if command -v podman &> /dev/null; then
        found=1
        if ! podman info &> /dev/null; then
            log_error "Podman est installé mais injoignable (machine arrêtée ou socket cassé)."
            log_error "  1) podman machine list   (la machine doit être « Currently running »)"
            log_error "  2) podman machine stop && podman machine start"
            log_error "  3) Si « already running » mais connexion refusée : pkill -f gvproxy; pkill -f vfkit; podman machine start"
            log_error "  4) podman system connection list   (le port doit correspondre à la machine)"
        elif ! podman compose version &> /dev/null; then
            log_error "Podman fonctionne mais 'podman compose' est indisponible : installez podman-compose (brew install podman-compose)."
        fi
    fi
    if command -v docker &> /dev/null; then
        found=1
        if ! docker info &> /dev/null; then
            log_error "Docker est installé mais le démon ne répond pas : lancez Docker Desktop et attendez qu'il soit prêt."
        elif ! docker compose version &> /dev/null; then
            log_error "Docker fonctionne mais le plugin 'docker compose' est absent : installez-le (inclus dans Docker Desktop)."
        fi
    fi
    if [ "$found" -eq 0 ]; then
        log_error "Ni Podman ni Docker n'est installé (brew install podman, ou Docker Desktop)."
    fi
}

# --- Commande doctor : état de l'environnement, sans rien démarrer ---
do_doctor() {
    local engine_ok=0 tool entry port name
    log_info "Diagnostic de l'environnement CampOrga"
    for tool in podman docker; do
        if command -v "$tool" &> /dev/null; then
            if "$tool" info &> /dev/null; then
                log_info "$tool : installé et joignable"
                engine_ok=1
            else
                log_warn "$tool : installé mais injoignable"
            fi
        else
            echo "   $tool : non installé"
        fi
    done
    if command -v podman &> /dev/null; then
        podman machine list 2> /dev/null | sed 's/^/   /' || true
    fi
    for entry in "8000:API" "5432:PostgreSQL" "27017:MongoDB" "5173:Frontend (Vite)"; do
        port="${entry%%:*}"
        name="${entry#*:}"
        if port_in_use "$port"; then
            echo "   Port $port ($name) : occupé (normal si CampOrga tourne déjà)"
        else
            echo "   Port $port ($name) : libre"
        fi
    done
    if [ -f ".env" ]; then
        log_info ".env : présent"
    else
        log_warn ".env : absent (il sera créé au prochain start)"
    fi
    if [ "$engine_ok" -eq 0 ]; then
        diagnose_engine
        log_error "Aucun moteur de conteneurs utilisable."
        return 1
    fi
    log_info "Environnement OK."
}

# --- Aide et diagnostic : ne nécessitent ni Docker ni Podman ---
case "${1:-}" in
    -h|--help|help) usage; exit 0 ;;
    doctor)         do_doctor; exit $? ;;
esac

# --- Détection de l'outil de conteneurisation ---
detect_container_tool() {
    if command -v podman &> /dev/null && podman compose version &> /dev/null; then
        echo "podman compose"
    elif command -v docker &> /dev/null && docker compose version &> /dev/null; then
        echo "docker compose"
    else
        log_error "Ni 'podman compose' ni 'docker compose' n'est utilisable."
        diagnose_engine
        log_error "Pour un état complet : ./camporga.sh doctor"
        exit 1
    fi
}

CONTAINER_CMD=$(detect_container_tool)
log_info "Outil de conteneurisation détecté : ${CONTAINER_CMD}"

# --- Analyse d'une erreur de démarrage : reconnaît les causes fréquentes ---
explain_error() {
    local text="$1" matched=0
    if echo "$text" | grep -qiE "address already in use|port is already allocated|ports are not available|bind: .*in use"; then
        log_error "Un port est déjà utilisé (8000 API, 5432 PostgreSQL ou 27017 MongoDB)."
        log_error "  Trouvez le coupable : lsof -i :8000 -i :5432 -i :27017 (puis arrêtez-le ou changez le port)."
        matched=1
    fi
    if echo "$text" | grep -qiE "no space left|disk quota"; then
        log_error "Espace disque insuffisant dans la machine de conteneurs."
        log_error "  Libérez de la place : $(echo "$CONTAINER_CMD" | cut -d' ' -f1) system prune (images et conteneurs inutilisés)."
        matched=1
    fi
    if echo "$text" | grep -qiE "out of memory|oomkilled|exit code 137|exited \(137\)"; then
        log_error "Mémoire insuffisante (processus tué par manque de RAM)."
        log_error "  Podman : podman machine stop && podman machine set --memory 4096 && podman machine start"
        log_error "  Docker Desktop : Settings > Resources > Memory."
        matched=1
    fi
    if echo "$text" | grep -qiE "cannot connect|connection refused|is the docker daemon running|unable to connect to .* socket"; then
        log_error "Le moteur de conteneurs ne répond plus."
        diagnose_engine
        matched=1
    fi
    if echo "$text" | grep -qiE "no such host|i/o timeout|tls handshake|temporary failure in name resolution|unable to retrieve auth|pull access denied|manifest unknown|dial tcp .*lookup"; then
        log_error "Problème réseau ou registre d'images : vérifiez la connexion Internet (le téléchargement des images a échoué)."
        matched=1
    fi
    if echo "$text" | grep -qiE "password authentication failed|role .* does not exist|database .* does not exist"; then
        log_error "Identifiants PostgreSQL incohérents : le .env ne correspond pas au volume existant."
        log_error "  Si ce sont des données de développement : ./camporga.sh cleanup (supprime les volumes), puis start."
        matched=1
    fi
    if echo "$text" | grep -qiE "UniqueViolation|can't locate revision|target database is not up to date|relation .* already exists"; then
        log_error "Erreur de migration Alembic : voir les lignes ci-dessus."
        log_error "  Base de développement : ./camporga.sh cleanup puis start. Sinon : $CONTAINER_CMD logs backend."
        matched=1
    fi
    if echo "$text" | grep -qiE "modulenotfounderror|no module named|importerror"; then
        log_error "Dépendance Python manquante : relancez ./camporga.sh start (reconstruit l'image) et vérifiez backend/requirements.txt."
        matched=1
    fi
    if echo "$text" | grep -qiE "validationerror|field required|secret_key"; then
        log_error "Configuration invalide : vérifiez le fichier .env (comparez avec .env.example)."
        matched=1
    fi
    if echo "$text" | grep -qiE "permission denied"; then
        log_error "Permission refusée : vérifiez les droits sur les dossiers montés (backend/, backups/)."
        matched=1
    fi
    [ "$matched" -eq 1 ]
}

# --- Le conteneur du service $1 est-il arrêté, en redémarrage ou en erreur ? ---
service_state_bad() {
    local out
    out=$($CONTAINER_CMD ps -a 2> /dev/null || $CONTAINER_CMD ps 2> /dev/null) || return 1
    echo "$out" | grep -E "[_-]$1[_-][0-9]+" | grep -qiE "exited|restarting|dead|unhealthy|stopped"
}

# --- Affiche les derniers logs d'un service en échec et cherche la cause ---
report_service_failure() {
    local svc="$1" logs
    log_error "Le service '$svc' ne démarre pas correctement. Dernières lignes de son journal :"
    logs=$($CONTAINER_CMD logs --tail 40 "$svc" 2>&1 || true)
    echo "$logs" | sed 's/^/    | /' >&2
    explain_error "$logs" || log_warn "Cause non reconnue. Journal complet : ./camporga.sh logs"
}

# --- Vérification du .env ---
# La fusion lit les secrets dans le .env à la RACINE (voir docker-compose.yml).
# S'il n'existe pas, on le crée depuis .env.example avec des secrets aléatoires.
check_env() {
    if [ ! -f ".env" ]; then
        if [ ! -f ".env.example" ]; then
            log_error ".env.example introuvable."
            exit 1
        fi
        log_warn "Le fichier .env n'existe pas. Création avec des secrets aléatoires..."
        cp .env.example .env
        gen() { python3 -c "import secrets; print(secrets.token_urlsafe($1))"; }
        sed -i "s/^SECRET_KEY=.*/SECRET_KEY=$(gen 48)/" .env
        sed -i "s/^MONGO_PASSWORD=.*/MONGO_PASSWORD=$(gen 24)/" .env
        sed -i "s/^POSTGRES_PASSWORD=.*/POSTGRES_PASSWORD=$(gen 24)/" .env
        log_info "Fichier .env créé (SECRET_KEY, POSTGRES_PASSWORD et MONGO_PASSWORD générés)."
    fi
}

# --- Attente de la base de données ---
wait_for_db() {
    log_info "Attente que la base de données soit prête..."
    local retries=30
    until $CONTAINER_CMD exec -T db sh -c 'pg_isready -U "$POSTGRES_USER"' > /dev/null 2>&1; do
        if service_state_bad db; then
            echo ""
            report_service_failure db
            exit 1
        fi
        sleep 1
        retries=$((retries - 1))
        if [ $retries -eq 0 ]; then
            echo ""
            log_error "La base de données n'est pas prête après 30 secondes."
            report_service_failure db
            exit 1
        fi
        echo -n "."
    done
    echo ""
    log_info "Base de données prête."
}

# --- Commandes Backend ---
wait_for_backend() {
    log_info "Attente que le backend soit prêt (migrations Alembic incluses)..."
    local retries=60
    until $CONTAINER_CMD exec -T backend python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/ready')" > /dev/null 2>&1; do
        if service_state_bad backend; then
            echo ""
            report_service_failure backend
            exit 1
        fi
        sleep 1
        retries=$((retries - 1))
        if [ $retries -eq 0 ]; then
            echo ""
            log_error "Le backend n'est pas prêt après 60 secondes."
            report_service_failure backend
            exit 1
        fi
        echo -n "."
    done
    echo ""
    log_info "Backend prêt."
}

do_start() {
    check_env
    log_info "Démarrage de PostgreSQL, MongoDB et FastAPI..."
    local up_log up_status
    up_log=$(mktemp)
    set +e
    $CONTAINER_CMD up -d --build 2>&1 | tee "$up_log"
    up_status=${PIPESTATUS[0]}
    set -e
    if [ "$up_status" -ne 0 ]; then
        echo ""
        log_error "Échec du démarrage des conteneurs (code $up_status)."
        explain_error "$(cat "$up_log")" || log_warn "Cause non reconnue : lisez les dernières lignes ci-dessus, ou lancez ./camporga.sh doctor."
        rm -f "$up_log"
        exit 1
    fi
    rm -f "$up_log"

    wait_for_db

    # Les migrations sont déjà appliquées par le conteneur au démarrage
    # (CMD du Dockerfile : alembic upgrade head && uvicorn ...). Les relancer ici
    # provoquait une course entre deux "alembic upgrade head" (UniqueViolation sur
    # alembic_version). On attend donc simplement que l'API réponde.
    wait_for_backend

    log_info "✅ CampOrga (backend) est prêt !"
    echo -e "   API    : http://localhost:8000"
    echo -e "   Docs   : http://localhost:8000/docs"
    echo -e "   Health : http://localhost:8000/health"
}

do_stop() {
    log_info "Arrêt des services backend et DB..."
    # `stop` échoue si les conteneurs n'existent plus (déjà supprimés, pod périmé...).
    # Ce n'est pas une vraie erreur : on nettoie alors les restes (pod, réseau)
    # au lieu d'afficher des erreurs puis un faux message de succès.
    if ! $CONTAINER_CMD stop > /dev/null 2>&1; then
        log_warn "Aucun conteneur actif à arrêter (déjà arrêtés ou supprimés). Nettoyage des restes..."
        $CONTAINER_CMD down --remove-orphans > /dev/null 2>&1 || true
    fi
    log_info "✅ Services arrêtés."
}

do_restart() {
    log_info "Redémarrage du backend..."
    if ! $CONTAINER_CMD restart backend; then
        report_service_failure backend
        exit 1
    fi
    log_info "✅ Backend redémarré."
}

do_cleanup() {
    log_warn "⚠️  ATTENTION : Cette action va supprimer TOUS les conteneurs et TOUTES les données de la base."
    read -p "Êtes-vous sûr de vouloir continuer ? (y/N) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        log_info "Nettoyage complet en cours..."
        $CONTAINER_CMD down -v --remove-orphans
        log_info "✅ Environnement nettoyé."
    else
        log_info "Nettoyage annulé."
    fi
}

do_test() {
    # Les tests tournent sur une base dédiée "camporga_test" : la base de
    # développement (vos camps, inscriptions, comptes) n'est jamais modifiée.
    log_info "Préparation de la base de test (camporga_test)..."
    $CONTAINER_CMD exec -T db sh -c 'psql -U "$POSTGRES_USER" -tAc "SELECT 1 FROM pg_database WHERE datname='"'"'camporga_test'"'"'" | grep -q 1 || createdb -U "$POSTGRES_USER" camporga_test'
    log_info "Lancement de la suite de tests..."
    # On reprend l'URL du backend (identifiants du .env) en remplaçant seulement le nom de la base.
    $CONTAINER_CMD exec backend sh -c 'DATABASE_URL="${DATABASE_URL%/*}/camporga_test" pytest --cov=app --cov-report=term-missing'
}

do_admin() {
    log_info "Vérification de l'existence d'un super admin..."
    ADMIN_EXISTS=$($CONTAINER_CMD exec -T backend python -c "
from app.db.session import SessionLocal
from app.models import User, UserRole

db = SessionLocal()
try:
    admin = db.query(User).filter(User.role == UserRole.SUPER_ADMIN).first()
    if admin:
        print(f'EXISTS|{admin.email}|{admin.first_name} {admin.last_name}|{admin.status.value}')
    else:
        print('NOT_FOUND')
finally:
    db.close()
" 2>/dev/null | grep -E "^(EXISTS|NOT_FOUND)" || true)

    if [ -z "$ADMIN_EXISTS" ]; then
        log_error "Impossible d'interroger la base : le backend est-il démarré ? (./camporga.sh start)"
        exit 1
    fi

    if [[ "$ADMIN_EXISTS" == EXISTS* ]]; then
        IFS='|' read -r _ email full_name status <<< "$ADMIN_EXISTS"
        log_warn "Un Super Admin existe déjà :"
        echo -e "   📧 Email : ${GREEN}${email}${NC}"
        echo -e "   👤 Nom   : ${full_name}"
        echo -e "   📊 Statut : ${status}"
        if [ "$email" = "admin@camporga.fr" ]; then
            echo -e "   🔑 Password par défaut : ${GREEN}ChangeMe123!${NC} (s'il n'a pas été changé)"
        fi
        echo -e "   (Mot de passe perdu ? ./camporga.sh admin-reset recrée admin@camporga.fr)"
    else
        log_info "Aucun Super Admin trouvé. Création du compte par défaut..."
        $CONTAINER_CMD exec backend python -c "
from app.core.security import hash_password
from app.db.session import SessionLocal
from app.models import User, UserRole, UserStatus

db = SessionLocal()
try:
    db.add(User(
        first_name='Admin',
        last_name='CampOrga',
        email='admin@camporga.fr',
        password_hash=hash_password('ChangeMe123!'),
        role=UserRole.SUPER_ADMIN,
        status=UserStatus.ACTIVE,
    ))
    db.commit()
    print('✅ Super Admin créé avec succès.')
    print('   📧 Email    : admin@camporga.fr')
    print('   🔑 Password : ChangeMe123!')
    print('   📊 Statut   : active')
except Exception as e:
    print(f'❌ Erreur : {e}')
finally:
    db.close()
"
    fi
}

do_admin_reset() {
    log_warn "⚠️  Cette action va SUPPRIMER le Super Admin existant et toutes ses données liées (camps, backups)."
    read -p "Continuer ? (y/N) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        log_info "Suppression des données liées au Super Admin..."
        $CONTAINER_CMD exec -T db sh -c 'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "$0"' "DELETE FROM backups WHERE triggered_by IN (SELECT id FROM users WHERE role = 'SUPER_ADMIN');" > /dev/null
        # Les clés étrangères n'ont pas de ON DELETE CASCADE en base (la cascade est gérée par l'ORM) :
        # on supprime d'abord les lignes qui dépendent des camps du super admin.
        for table in registrations camp_modalities landing_pages contact_messages; do
            $CONTAINER_CMD exec -T db sh -c 'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "$0"' "DELETE FROM $table WHERE camp_id IN (SELECT c.id FROM camps c JOIN users u ON u.id = c.organizer_id WHERE u.role = 'SUPER_ADMIN');" > /dev/null
        done
        $CONTAINER_CMD exec -T db sh -c 'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "$0"' "DELETE FROM camps WHERE organizer_id IN (SELECT id FROM users WHERE role = 'SUPER_ADMIN');" > /dev/null
        $CONTAINER_CMD exec -T db sh -c 'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "$0"' "DELETE FROM users WHERE role = 'SUPER_ADMIN';" > /dev/null
        
        log_info "Création du nouveau Super Admin..."
        $CONTAINER_CMD exec backend python -c "
from app.core.security import hash_password
from app.db.session import SessionLocal
from app.models import User, UserRole, UserStatus

db = SessionLocal()
try:
    db.add(User(
        first_name='Admin',
        last_name='CampOrga',
        email='admin@camporga.fr',
        password_hash=hash_password('ChangeMe123!'),
        role=UserRole.SUPER_ADMIN,
        status=UserStatus.ACTIVE,
    ))
    db.commit()
    print('✅ Super Admin recréé avec succès.')
    print('   📧 Email    : admin@camporga.fr')
    print('   🔑 Password : ChangeMe123!')
    print('   📊 Statut   : active')
except Exception as e:
    print(f'❌ Erreur : {e}')
finally:
    db.close()
"
    else
        log_info "Annulé."
    fi
}

# --- Commandes Frontend ---
do_frontend() {
    if [ ! -d "frontend" ]; then
        log_error "Le dossier 'frontend/' n'existe pas."
        exit 1
    fi

    # Installe les dépendances si node_modules est absent OU plus ancien que
    # package.json / package-lock.json (ex. après un git pull ou un merge).
    if [ ! -d "frontend/node_modules" ] \
       || [ "frontend/package.json" -nt "frontend/node_modules/.package-lock.json" ] \
       || [ "frontend/package-lock.json" -nt "frontend/node_modules/.package-lock.json" ]; then
        log_warn "Les dépendances npm sont absentes ou obsolètes. Installation..."
        (cd frontend && npm install) || { log_error "Échec de npm install."; exit 1; }
    fi

    if port_in_use 5173; then
        log_warn "Le port 5173 est déjà utilisé. Un serveur Vite tourne peut-être déjà."
        log_info "Pour l'arrêter : ./camporga.sh frontend-stop"
        exit 1
    fi

    log_info "Démarrage du frontend (Vite) sur http://localhost:5173..."
    cd frontend
    npm run dev
    cd ..
}

do_frontend_stop() {
    if ! port_in_use 5173; then
        log_info "Aucun serveur Vite ne tourne sur le port 5173."
        return
    fi

    log_info "Arrêt du serveur Vite (port 5173)..."
    if command -v lsof &> /dev/null; then
        lsof -ti:5173 | xargs kill -9 2>/dev/null || true
    else
        fuser -k 5173/tcp > /dev/null 2>&1 || true
    fi
    log_info "✅ Frontend arrêté."
}

# --- Formatage ---
do_format() {
    log_info "Formatage du code Python..."
    $CONTAINER_CMD exec backend sh -c "pip install -q ruff black && ruff check --fix app tests && black app tests"
    log_info "✅ Code formaté."
}

# --- Logs ---
do_logs() {
    log_info "Affichage des logs du backend (Ctrl+C pour quitter)..."
    $CONTAINER_CMD logs -f backend
}

# --- Statut ---
do_ps() {
    $CONTAINER_CMD ps
    echo ""
    if port_in_use 5173; then
        log_info "Frontend : ✅ Vite tourne sur le port 5173"
    else
        log_info "Frontend : ⏹️  Vite n'est pas lancé"
    fi
}

# --- Menu ---
case "$1" in
    start)          do_start ;;
    stop)           do_stop ;;
    restart)        do_restart ;;
    cleanup)        do_cleanup ;;
    test)           do_test ;;
    admin)          do_admin ;;
    admin-reset)    do_admin_reset ;;
    frontend)       do_frontend ;;
    frontend-stop)  do_frontend_stop ;;
    format)         do_format ;;
    logs)           do_logs ;;
    ps)             do_ps ;;
    *)
        usage
        exit 1
        ;;
esac