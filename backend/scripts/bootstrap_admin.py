import os  # Module standard pour lire les variables d'environnement.
import sys  # Module standard pour écrire sur la sortie d'erreur et quitter avec un code.

from sqlalchemy.exc import IntegrityError  # Exception levée par SQLAlchemy en cas de violation de contrainte (ex. email unique).

from app.core.security import hash_password  # Fonction qui transforme le mot de passe en hash sécurisé.
from app.db.session import SessionLocal  # Fabrique de sessions de base de données.
from app.models import User, UserRole, UserStatus  # Modèle utilisateur, rôles et statuts possibles.

def main() -> int:  # Point d'entrée du script ; renvoie un code de sortie (0 = succès).
    email = os.environ.get("BOOTSTRAP_ADMIN_EMAIL", "").strip()  # Lit l'email de l'admin, chaîne vide si absent, sans espaces autour.
    password = os.environ.get("BOOTSTRAP_ADMIN_PASSWORD", "")  # Lit le mot de passe brut (non modifié, les espaces comptent).
    first_name = os.environ.get("BOOTSTRAP_ADMIN_FIRST_NAME", "Super").strip()  # Prénom, valeur par défaut « Super ».
    last_name = os.environ.get("BOOTSTRAP_ADMIN_LAST_NAME", "Admin").strip()  # Nom, valeur par défaut « Admin ».

    if not email or len(password) < 12:  # Refuse un email vide ou un mot de passe de moins de 12 caractères.
        print(  # Affiche l'aide sur la sortie d'erreur.
            "Set BOOTSTRAP_ADMIN_EMAIL and BOOTSTRAP_ADMIN_PASSWORD "
            "(at least 12 characters).",
            file=sys.stderr,
        )
        return 2  # Code 2 : configuration invalide.

    db = SessionLocal()  # Ouvre une session de base de données.
    try:
        existing = db.query(User).filter(User.email == email).first()  # Cherche un utilisateur avec cet email (None si absent).
        if existing is not None:  # Un compte existe déjà avec cet email.
            if existing.role != UserRole.SUPER_ADMIN:  # Ce compte n'est pas super admin : on ne le modifie pas.
                print("The configured email belongs to a non-super-admin account.", file=sys.stderr)
                return 1  # Code 1 : conflit à résoudre manuellement.
            print(f"Super-admin already exists: {email}")  # Le super admin existe déjà : opération idempotente.
            return 0  # Succès sans rien créer.

        db.add(  # Prépare l'insertion du nouveau super admin.
            User(
                email=email,  # Email de connexion.
                password_hash=hash_password(password),  # Stocke uniquement le hash, jamais le mot de passe en clair.
                first_name=first_name,
                last_name=last_name,
                role=UserRole.SUPER_ADMIN,  # Rôle le plus élevé de l'application.
                status=UserStatus.ACTIVE,  # Compte actif, utilisable immédiatement.
            )
        )
        db.commit()  # Valide l'insertion en base.
        print(f"Created initial super-admin: {email}")  # Confirme la création.
        return 0  # Succès.
    except IntegrityError:  # Une contrainte de base a été violée (par exemple une création concurrente avec le même email).
        db.rollback()  # Annule la transaction en cours pour laisser la base dans un état propre.
        print("Could not create the bootstrap super-admin due to a database conflict.", file=sys.stderr)
        return 1  # Code 1 : échec de création.
    finally:  # Exécuté dans tous les cas, succès ou erreur.
        db.close()  # Libère la connexion à la base.

if __name__ == "__main__":  # Ce bloc ne s'exécute que si le fichier est lancé directement (python script.py), pas lors d'un import.
    raise SystemExit(main())  # Lance main() et transmet son code de retour au système.