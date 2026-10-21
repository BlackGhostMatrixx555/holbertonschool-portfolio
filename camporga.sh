#!/usr/bin/env bash

# ==============================================================================
# CampOrga — Script de gestion du cycle de vie
# ==============================================================================
# Ce script permet de démarrer, arrêter, nettoyer et tester l'environnement
# de développement complet (PostgreSQL + FastAPI) via Docker Compose.
#
# Usage :
#   ./camporga.sh start     # Démarre les services et applique les migrations
#   ./camporga.sh stop      # Arrête les services (garde les données)
#   ./camporga.sh restart   # Redémarre le backend
#   ./camporga.sh cleanup   # Détruit tout (conteneurs + base de données)
#   ./camporga.sh test      # Lance la suite de tests (55 tests) avec couverture
#   ./camporga.sh admin     # Crée le super admin par défaut
#   ./camporga.sh format    # Formate le code Python avec Ruff et Black
#   ./camporga.sh logs      # Affiche les logs du backend en temps réel
#   ./camporga.sh ps        # Affiche l'état des services
# ==============================================================================

set -e # Arrête le script en cas d'erreur

# Couleurs pour le terminal
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Fonction d'affichage
log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Vérifie que Docker est en cours d'exécution
check_docker() {
    if ! docker info > /dev/null 2>&1; then
        log_error "Docker n'est pas en cours d'exécution. Lancez Docker Desktop et réessayez."
        exit 1
    fi
}

# Vérifie que le fichier .env existe
check_env() {
    if [ ! -f "backend/.env" ]; then
        log_warn "Le fichier backend/.env n'existe pas. Création à partir de .env.example..."
        if [ -f "backend/.env.example" ]; then
            cp backend/.env.example backend/.env
            log_info "Fichier .env créé. N'oubliez pas d'y ajouter une vraie SECRET_KEY !"
        else
            log_error "backend/.env.example est introuvable. Impossible de continuer."
            exit 1
        fi
    fi
}

# Démarre les services
do_start() {
    check_docker
    check_env
    
    log_info "Démarrage de PostgreSQL et FastAPI..."
    docker compose up -d --build

    log_info "Attente que la base de données soit prête..."
    # Boucle simple pour attendre que le healthcheck de la DB passe
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

# Arrête les services (sans perdre les données)
do_stop() {
    check_docker
    log_info "Arrêt des services..."
    docker compose stop
    log_info "✅ Services arrêtés (les données sont conservées)."
}

# Redémarre uniquement le backend (utile après une modification de code)
do_restart() {
    check_docker
    log_info "Redémarrage du backend..."
    docker compose restart backend
    log_info "✅ Backend redémarré."
}

# Détruit tout (ATTENTION : perte de données)
do_cleanup() {
    check_docker
    log_warn "⚠️  ATTENTION : Cette action va supprimer TOUS les conteneurs et TOUTES les données de la base."
    read -p "Êtes-vous sûr de vouloir continuer ? (y/N) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        log_info "Nettoyage complet en cours..."
        docker compose down -v --remove-orphans
        log_info "✅ Environnement nettoyé. Vous pouvez relancer avec './camporga.sh start'."
    else
        log_info "Nettoyage annulé."
    fi
}

# Lance les tests avec couverture
do_test() {
    check_docker
    log_info "Lancement de la suite de tests (55 tests attendus)..."
    docker compose exec backend pytest --cov=app --cov-report=term-missing
}

# Crée le super admin par défaut
do_admin() {
    check_docker
    log_info "Création du super admin par défaut..."
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
    print('✅ Super admin créé : admin@camporga.fr / ChangeMe123!')
except Exception as e:
    print(f'⚠️ Erreur (le compte existe peut-être déjà) : {e}')
finally:
    db.close()
"
}

# Formate le code (Ruff + Black)
do_format() {
    check_docker
    log_info "Formatage du code Python..."
    docker compose exec backend ruff check --fix app tests
    docker compose exec backend black app tests
    log_info "✅ Code formaté."
}

# Affiche les logs
do_logs() {
    check_docker
    log_info "Affichage des logs du backend (Ctrl+C pour quitter)..."
    docker compose logs -f backend
}

# Affiche l'état
do_ps() {
    check_docker
    docker compose ps
}

# Menu principal
case "$1" in
    start)   do_start ;;
    stop)    do_stop ;;
    restart) do_restart ;;
    cleanup) do_cleanup ;;
    test)    do_test ;;
    admin)   do_admin ;;
    format)  do_format ;;
    logs)    do_logs ;;
    ps)      do_ps ;;
    *)
        echo "Usage: $0 {start|stop|restart|cleanup|test|admin|format|logs|ps}"
        echo ""
        echo "  start    : Démarre les services et applique les migrations"
        echo "  stop     : Arrête les services (garde les données)"
        echo "  restart  : Redémarre le backend"
        echo "  cleanup  : Détruit tout (conteneurs + base de données)"
        echo "  test     : Lance la suite de tests avec couverture"
        echo "  admin    : Crée le super admin par défaut (admin@camporga.fr)"
        echo "  format   : Formate le code Python (Ruff + Black)"
        echo "  logs     : Affiche les logs du backend en temps réel"
        echo "  ps       : Affiche l'état des services"
        exit 1
        ;;
esac
