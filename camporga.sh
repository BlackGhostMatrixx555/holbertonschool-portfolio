#!/usr/bin/env bash

# ==============================================================================
# CampOrga — Script de gestion du cycle de vie (Docker/Podman + Frontend)
# ==============================================================================

set -e

# --- Couleurs ---
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
BOLD='\033[1m'
NC='\033[0m'

log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# --- Détection de l'outil de conteneurisation ---
detect_container_tool() {
    if command -v podman &> /dev/null && podman compose version &> /dev/null; then
        echo "podman compose"
    elif command -v docker &> /dev/null && docker compose version &> /dev/null; then
        echo "docker compose"
    else
        log_error "Ni 'podman compose' ni 'docker compose' n'est installé."
        exit 1
    fi
}

CONTAINER_CMD=$(detect_container_tool)
log_info "Outil de conteneurisation détecté : ${CONTAINER_CMD}"

# --- Vérification du .env ---
check_env() {
    if [ ! -f "backend/.env" ]; then
        log_warn "Le fichier backend/.env n'existe pas. Création..."
        if [ -f "backend/.env.example" ]; then
            cp backend/.env.example backend/.env
            log_info "Fichier .env créé. N'oubliez pas d'y ajouter une vraie SECRET_KEY !"
        else
            log_error "backend/.env.example introuvable."
            exit 1
        fi
    fi
}

# --- Attente de la base de données ---
wait_for_db() {
    log_info "Attente que la base de données soit prête..."
    local retries=30
    until $CONTAINER_CMD exec -T db pg_isready -U camporga > /dev/null 2>&1; do
        sleep 1
        retries=$((retries - 1))
        if [ $retries -eq 0 ]; then
            log_error "La base de données n'est pas prête après 30 secondes."
            exit 1
        fi
        echo -n "."
    done
    echo ""
    log_info "Base de données prête."
}

# --- Commandes Backend ---
do_start() {
    check_env
    log_info "Démarrage de PostgreSQL et FastAPI..."
    $CONTAINER_CMD up -d --build

    wait_for_db

    log_info "Application des migrations Alembic..."
    $CONTAINER_CMD exec backend alembic upgrade head

    log_info "✅ CampOrga (backend) est prêt !"
    echo -e "   API    : http://localhost:8000"
    echo -e "   Docs   : http://localhost:8000/docs"
    echo -e "   Health : http://localhost:8000/health"
}

do_stop() {
    log_info "Arrêt des services backend et DB..."
    $CONTAINER_CMD stop
    log_info "✅ Services backend arrêtés."
}

do_restart() {
    log_info "Redémarrage du backend..."
    $CONTAINER_CMD restart backend
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
    log_info "Nettoyage de la base de données (pour un environnement de test propre)..."
    $CONTAINER_CMD exec -T db psql -U camporga -c "
        TRUNCATE TABLE payments, registrations, contact_messages, landing_pages, camp_modalities, camps, backups, users RESTART IDENTITY CASCADE;
    " > /dev/null 2>&1
    log_info "Base nettoyée."
    
    log_info "Lancement de la suite de tests..."
    $CONTAINER_CMD exec backend pytest --cov=app --cov-report=term-missing
}

do_admin() {
    log_info "Vérification de l'existence d'un super admin..."
    ADMIN_EXISTS=$($CONTAINER_CMD exec -T backend python -c "
from app.database import SessionLocal
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
" 2>/dev/null | grep -E "^(EXISTS|NOT_FOUND)")

    if [[ "$ADMIN_EXISTS" == EXISTS* ]]; then
        IFS='|' read -r _ email full_name status <<< "$ADMIN_EXISTS"
        log_warn "Un Super Admin existe déjà :"
        echo -e "   📧 Email : ${GREEN}${email}${NC}"
        echo -e "   👤 Nom   : ${full_name}"
        echo -e "   📊 Statut : ${status}"
        echo -e "   🔑 Password par défaut : ${GREEN}ChangeMe123!${NC}"
        echo -e "   (Si vous l'avez changé, utilisez admin-reset pour le réinitialiser)"
    else
        log_info "Aucun Super Admin trouvé. Création du compte par défaut..."
        $CONTAINER_CMD exec backend python -c "
from app.database import SessionLocal
from app.models import UserRole, UserStatus
from app.schemas.user import UserCreate
from app.services.user_service import UserService

db = SessionLocal()
try:
    user = UserService(db).create(UserCreate(
        first_name='Admin',
        last_name='CampOrga',
        email='admin@camporga.fr',
        password='ChangeMe123!',
        role=UserRole.SUPER_ADMIN,
    ))
    user.status = UserStatus.ACTIVE
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
        $CONTAINER_CMD exec -T db psql -U camporga -c "DELETE FROM backups WHERE triggered_by IN (SELECT id FROM users WHERE role = 'super_admin');" > /dev/null
        $CONTAINER_CMD exec -T db psql -U camporga -c "DELETE FROM camps WHERE organizer_id IN (SELECT id FROM users WHERE role = 'super_admin');" > /dev/null
        $CONTAINER_CMD exec -T db psql -U camporga -c "DELETE FROM users WHERE role = 'super_admin';" > /dev/null
        
        log_info "Création du nouveau Super Admin..."
        $CONTAINER_CMD exec backend python -c "
from app.database import SessionLocal
from app.models import UserRole, UserStatus
from app.schemas.user import UserCreate
from app.services.user_service import UserService

db = SessionLocal()
try:
    user = UserService(db).create(UserCreate(
        first_name='Admin',
        last_name='CampOrga',
        email='admin@camporga.fr',
        password='ChangeMe123!',
        role=UserRole.SUPER_ADMIN,
    ))
    user.status = UserStatus.ACTIVE
    db.commit()
    print('✅ Super Admin recréé avec succès.')
    print('   📧 Email    : admin@camporga.fr')
    print('   🔑 Password : ChangeMe123!')
    print('   📊 Statut   : active')
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

    if [ ! -d "frontend/node_modules" ]; then
        log_warn "Les dépendances npm ne sont pas installées. Installation..."
        cd frontend && npm install && cd ..
    fi

    if lsof -ti:5173 > /dev/null 2>&1; then
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
    if ! lsof -ti:5173 > /dev/null 2>&1; then
        log_info "Aucun serveur Vite ne tourne sur le port 5173."
        return
    fi

    log_info "Arrêt du serveur Vite (port 5173)..."
    lsof -ti:5173 | xargs kill -9 2>/dev/null || true
    log_info "✅ Frontend arrêté."
}

# --- Formatage ---
do_format() {
    log_info "Formatage du code Python..."
    $CONTAINER_CMD exec backend ruff check --fix app tests
    $CONTAINER_CMD exec backend black app tests
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
    if lsof -ti:5173 > /dev/null 2>&1; then
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
        echo "Usage: $0 {start|stop|restart|cleanup|test|admin|admin-reset|frontend|frontend-stop|format|logs|ps}"
        echo ""
        echo "  start          : Démarre les services backend + DB"
        echo "  stop           : Arrête les services backend + DB"
        echo "  restart        : Redémarre le backend"
        echo "  cleanup        : Détruit tout (conteneurs + base)"
        echo "  test           : Lance la suite de tests avec couverture"
        echo "  admin          : Crée le Super Admin (ou affiche celui qui existe)"
        echo "  admin-reset    : Supprime et recrée le Super Admin"
        echo "  frontend       : Démarre le serveur Vite (bloquant, Ctrl+C pour quitter)"
        echo "  frontend-stop  : Arrête le serveur Vite (port 5173)"
        echo "  format         : Formate le code Python"
        echo "  logs           : Affiche les logs du backend"
        echo "  ps             : Affiche l'état des services"
        exit 1
        ;;
esac