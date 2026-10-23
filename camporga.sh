#!/usr/bin/env bash

# ==============================================================================
# CampOrga — Script de gestion du cycle de vie
# ==============================================================================

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

check_docker() {
    if ! docker info > /dev/null 2>&1; then
        log_error "Docker n'est pas en cours d'exécution."
        exit 1
    fi
}

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

do_start() {
    check_docker
    check_env
    log_info "Démarrage de PostgreSQL et FastAPI..."
    docker compose up -d --build

    log_info "Attente que la base de données soit prête..."
    until docker compose exec -T db pg_isready -U camporga > /dev/null 2>&1; do
        echo -n "."
        sleep 1
    done
    echo ""

    log_info "Application des migrations Alembic..."
    docker compose exec backend alembic upgrade head

    log_info "✅ CampOrga est prêt !"
    echo -e "   API    : http://localhost:8000"
    echo -e "   Docs   : http://localhost:8000/docs"
    echo -e "   Health : http://localhost:8000/health"
}

do_stop() {
    check_docker
    log_info "Arrêt des services..."
    docker compose stop
    log_info "✅ Services arrêtés."
}

do_restart() {
    check_docker
    log_info "Redémarrage du backend..."
    docker compose restart backend
    log_info "✅ Backend redémarré."
}

do_cleanup() {
    check_docker
    log_warn "⚠️  ATTENTION : Cette action va supprimer TOUS les conteneurs et TOUTES les données de la base."
    read -p "Êtes-vous sûr de vouloir continuer ? (y/N) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        log_info "Nettoyage complet en cours..."
        docker compose down -v --remove-orphans
        log_info "✅ Environnement nettoyé."
    else
        log_info "Nettoyage annulé."
    fi
}

do_test() {
    check_docker
    log_info "Lancement de la suite de tests (67 tests attendus)..."
    docker compose exec backend pytest --cov=app --cov-report=term-missing
}

do_admin() {
    check_docker
    
    # Vérifier si un super admin existe déjà
    log_info "Vérification de l'existence d'un super admin..."
    ADMIN_EXISTS=$(docker compose exec -T backend python -c "
from app.database import SessionLocal
from app.models import User, UserRole

db = SessionLocal()
try:
    admin = db.query(User).filter(User.role == UserRole.SUPER_ADMIN).first()
    if admin:
        print(f'EXISTS|{admin.email}|{admin.first_name} {admin.last_name}')
    else:
        print('NOT_FOUND')
finally:
    db.close()
" 2>/dev/null | grep -E "^(EXISTS|NOT_FOUND)")

    if [[ "$ADMIN_EXISTS" == EXISTS* ]]; then
        IFS='|' read -r _ email full_name <<< "$ADMIN_EXISTS"
        log_warn "Un Super Admin existe déjà :"
        echo -e "   📧 Email : ${GREEN}${email}${NC}"
        echo -e "   👤 Nom   : ${full_name}"
        log_info "Pour changer les identifiants, utilisez : ./camporga.sh admin-reset"
    else
        log_info "Aucun Super Admin trouvé. Création du compte par défaut..."
        docker compose exec backend python -c "
from app.database import SessionLocal
from app.models import UserRole
from app.schemas.user import UserCreate
from app.services.user_service import UserService

db = SessionLocal()
try:
    UserService(db).create(UserCreate(
        first_name='Admin',
        last_name='CampOrga',
        email='admin@camporga.fr',
        password='ChangeMe123!',
        role=UserRole.SUPER_ADMIN,
    ))
    print('✅ Super Admin créé avec succès.')
    print('   📧 Email    : admin@camporga.fr')
    print('   🔑 Password : ChangeMe123!')
    print('   ⚠️  Changez ce mot de passe après la première connexion !')
except Exception as e:
    print(f'❌ Erreur : {e}')
finally:
    db.close()
"
    fi
}

do_admin_reset() {
    check_docker
    log_warn "⚠️  Cette action va SUPPRIMER le Super Admin existant et toutes ses données liées (camps, backups)."
    read -p "Continuer ? (y/N) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        log_info "Suppression des données liées au Super Admin..."
        docker compose exec -T db psql -U camporga -c "DELETE FROM backups WHERE triggered_by IN (SELECT id FROM users WHERE role = 'super_admin');" > /dev/null
        docker compose exec -T db psql -U camporga -c "DELETE FROM camps WHERE organizer_id IN (SELECT id FROM users WHERE role = 'super_admin');" > /dev/null
        docker compose exec -T db psql -U camporga -c "DELETE FROM users WHERE role = 'super_admin';" > /dev/null
        
        log_info "Création du nouveau Super Admin..."
        docker compose exec backend python -c "
from app.database import SessionLocal
from app.models import UserRole
from app.schemas.user import UserCreate
from app.services.user_service import UserService

db = SessionLocal()
try:
    UserService(db).create(UserCreate(
        first_name='Admin',
        last_name='CampOrga',
        email='admin@camporga.fr',
        password='ChangeMe123!',
        role=UserRole.SUPER_ADMIN,
    ))
    print('✅ Super Admin recréé.')
    print('   📧 Email    : admin@camporga.fr')
    print('   🔑 Password : ChangeMe123!')
finally:
    db.close()
"
    else
        log_info "Annulé."
    fi
}

do_format() {
    check_docker
    log_info "Formatage du code Python..."
    docker compose exec backend ruff check --fix app tests
    docker compose exec backend black app tests
    log_info "✅ Code formaté."
}

do_logs() {
    check_docker
    log_info "Affichage des logs du backend (Ctrl+C pour quitter)..."
    docker compose logs -f backend
}

do_ps() {
    check_docker
    docker compose ps
}

case "$1" in
    start)        do_start ;;
    stop)         do_stop ;;
    restart)      do_restart ;;
    cleanup)      do_cleanup ;;
    test)         do_test ;;
    admin)        do_admin ;;
    admin-reset)  do_admin_reset ;;
    format)       do_format ;;
    logs)         do_logs ;;
    ps)           do_ps ;;
    *)
        echo "Usage: $0 {start|stop|restart|cleanup|test|admin|admin-reset|format|logs|ps}"
        echo ""
        echo "  start        : Démarre les services et applique les migrations"
        echo "  stop         : Arrête les services (garde les données)"
        echo "  restart      : Redémarre le backend"
        echo "  cleanup      : Détruit tout (conteneurs + base)"
        echo "  test         : Lance la suite de tests avec couverture"
        echo "  admin        : Crée le Super Admin (ou affiche celui qui existe)"
        echo "  admin-reset  : Supprime et recrée le Super Admin"
        echo "  format       : Formate le code Python"
        echo "  logs         : Affiche les logs du backend"
        echo "  ps           : Affiche l'état des services"
        exit 1
        ;;
esac
