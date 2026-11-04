#!/usr/bin/env python3
# Shebang : exécute ce fichier avec l'interpréteur python3 présent dans le PATH.
"""
CampOrga — Outil de visualisation de dépôt (tree + cat)

Génère un fichier texte contenant :
  1. L'arborescence complète du projet (comme `tree`).
  2. Le contenu de tous les fichiers texte (comme `cat`).

Les rapports sont automatiquement stockés dans le dossier `scripts/rapports/`.

Usage:
    python3 scripts/visualize_repo.py <chemin_du_projet> [--output <fichier>]

Exemples:
    python3 scripts/visualize_repo.py ~/Documents/Holberton/Portfolio/holbertonschool-portfolio-collins
    python3 scripts/visualize_repo.py . --output mon_repo.txt
"""
# Docstring du module : documente le rôle, l'usage et des exemples (accessible via help()).

import sys            # Accès à sys.exit() pour quitter avec un code d'erreur.
import os             # Importé mais non utilisé dans le script.
import argparse       # Gestion des arguments de ligne de commande.
from pathlib import Path   # Manipulation de chemins de façon orientée objet.
from datetime import datetime  # Horodatage pour le nom de fichier et l'en-tête.

# --- Configuration ---
# Extensions de fichiers texte à inclure dans le `cat`
# Un ensemble (set) permet une recherche en temps constant avec `in`.
TEXT_EXTENSIONS = {
    ".py", ".ts", ".tsx", ".js", ".jsx", ".json", ".md", ".txt",
    ".yml", ".yaml", ".html", ".css", ".sql", ".sh", ".toml", ".ini",
    ".env", ".example", ".gitignore", ".dockerignore", ".mako",
}
# Note : ".env" peut contenir des secrets ; voir les remarques de sécurité ci-dessous.

# Dossiers à ignorer (volumineux et inutiles)
IGNORED_DIRS = {
    "node_modules", ".git", "__pycache__", ".venv", "venv",
    "dist", "build", ".pytest_cache", ".vite", ".next", ".cache",
    ".mypy_cache", ".ruff_cache", "coverage", ".nyc_output",
    ".idea", ".vscode", ".DS_Store", "rapports",
}
# "rapports" est exclu pour éviter d'inclure les anciens rapports générés.

# Fichiers à ignorer (binaires ou trop volumineux)
IGNORED_FILES = {
    ".DS_Store", "package-lock.json", "yarn.lock", "pnpm-lock.yaml",
    "poetry.lock", "Pipfile.lock",
}
# Fichiers de verrouillage : très volumineux et peu utiles à relire.

# Taille max d'un fichier à inclure (en Ko)
MAX_FILE_SIZE_KB = 500

# Dossier où sont stockés les rapports
REPORTS_DIR_NAME = "rapports"

def should_ignore_dir(dir_name: str) -> bool:
    """Vérifie si un dossier doit être ignoré."""
    # Compare seulement le nom (pas le chemin complet) avec la liste d'exclusion.
    return dir_name in IGNORED_DIRS

def should_ignore_file(file_path: Path) -> bool:
    """Vérifie si un fichier doit être ignoré."""
    # Exclusion par nom exact.
    if file_path.name in IGNORED_FILES:
        return True
    # Ignorer les fichiers binaires connus (par extension, insensible à la casse grâce à .lower()).
    if file_path.suffix.lower() in {".png", ".jpg", ".jpeg", ".gif", ".svg", ".ico",
                                     ".pdf", ".zip", ".tar", ".gz", ".mp4", ".mp3",
                                     ".woff", ".woff2", ".ttf", ".eot", ".pyc"}:
        return True
    # Ignorer les fichiers trop volumineux.
    try:
        # stat().st_size renvoie la taille en octets ; on compare à la limite convertie en octets.
        if file_path.stat().st_size > MAX_FILE_SIZE_KB * 1024:
            return True
    except OSError:
        # Fichier inaccessible (lien cassé, permissions...) : on l'ignore par précaution.
        return True
    return False

def is_text_file(file_path: Path) -> bool:
    """Vérifie si un fichier est un fichier texte (par extension)."""
    # Teste l'extension (ex. ".py") ou le nom complet (ex. ".gitignore", qui n'a pas de suffixe).
    return file_path.suffix.lower() in TEXT_EXTENSIONS or file_path.name in TEXT_EXTENSIONS

def generate_tree(root: Path) -> list[str]:
    """Génère l'arborescence du projet (comme `tree`)."""
    # Syntaxe list[str] : annotation de type moderne (Python 3.9+).
    lines = []
    # En-tête du rapport : nom du projet, date de génération, chemin absolu.
    lines.append(f"# Arborescence — {root.name}")
    lines.append(f"Généré le : {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    lines.append(f"Chemin : {root}")
    lines.append("=" * 70)
    lines.append("")

    def walk(directory: Path, prefix: str = ""):
        # Fonction récursive interne : parcourt un dossier et ses sous-dossiers.
        # prefix contient l'indentation accumulée (│, espaces) pour dessiner l'arbre.
        try:
            # Liste le contenu ; tri : dossiers d'abord (not is_dir() vaut False pour eux), puis nom en minuscules.
            entries = sorted(directory.iterdir(), key=lambda e: (not e.is_dir(), e.name.lower()))
        except PermissionError:
            # Dossier non lisible : on passe sans interrompre le parcours.
            return

        # Filtrer les dossiers et fichiers ignorés.
        entries = [e for e in entries if not (e.is_dir() and should_ignore_dir(e.name))]
        entries = [e for e in entries if not (e.is_file() and should_ignore_file(e))]

        for i, entry in enumerate(entries):
            is_last = (i == len(entries) - 1)  # Vrai pour le dernier élément du dossier.
            # "└── " pour le dernier élément, "├── " sinon : caractères de dessin d'arbre.
            connector = "└── " if is_last else "├── "
            icon = "📁" if entry.is_dir() else "📄"
            lines.append(f"{prefix}{connector}{icon} {entry.name}")

            if entry.is_dir():
                # Pour les enfants : pas de barre verticale après le dernier élément, sinon une barre.
                extension = "    " if is_last else "│   "
                walk(entry, prefix + extension)  # Appel récursif avec l'indentation mise à jour.

    walk(root)  # Lance le parcours depuis la racine.
    return lines

def generate_content(root: Path) -> list[str]:
    """Génère le contenu de tous les fichiers texte (comme `cat`)."""
    lines = []
    # Bandeau de section.
    lines.append("")
    lines.append("=" * 70)
    lines.append("# Contenu des fichiers")
    lines.append("=" * 70)
    lines.append("")

    # rglob("*") parcourt récursivement tous les chemins ; sorted() les ordonne alphabétiquement.
    for file_path in sorted(root.rglob("*")):
        if not file_path.is_file():
            continue  # On ne traite que les fichiers, pas les dossiers.
        if should_ignore_file(file_path):
            continue
        if not is_text_file(file_path):
            continue  # Seuls les fichiers texte connus sont lus.
        # Ignorer le dossier des rapports.
        # Note : rglob descend aussi dans les dossiers ignorés (node_modules, .git...) ;
        # seul le test sur "rapports" est fait ici, pas sur IGNORED_DIRS.
        if REPORTS_DIR_NAME in file_path.parts:
            continue

        # Chemin relatif à la racine, pour un affichage plus lisible.
        rel_path = file_path.relative_to(root)
        lines.append("")
        lines.append("=" * 70)
        lines.append(f"📄 FICHIER : {rel_path}")
        lines.append("=" * 70)

        try:
            # Lecture en UTF-8 ; errors="ignore" écarte silencieusement les octets invalides.
            content = file_path.read_text(encoding="utf-8", errors="ignore")
            lines.append(content)
        except Exception as e:
            # Toute autre erreur de lecture est consignée dans le rapport au lieu de planter le script.
            lines.append(f"[Erreur de lecture : {e}]")

    return lines

def main():
    # Point d'entrée : configuration des arguments de la ligne de commande.
    parser = argparse.ArgumentParser(description="Visualiser un dépôt (tree + cat)")
    parser.add_argument("path", help="Chemin du projet à visualiser")  # Argument positionnel obligatoire.
    parser.add_argument("--output", "-o", help="Nom du fichier de sortie (sera placé dans scripts/rapports/)")  # Option facultative.
    args = parser.parse_args()  # Lit et valide les arguments fournis.

    # expanduser() transforme "~" en dossier personnel ; resolve() donne un chemin absolu normalisé.
    root = Path(args.path).expanduser().resolve()
    if not root.exists():
        print(f"❌ Le dossier '{root}' n'existe pas.")
        sys.exit(1)  # Sortie avec code d'erreur.

    # Déterminer le dossier des rapports (à côté du script).
    script_dir = Path(__file__).parent.resolve()  # Dossier contenant ce script.
    reports_dir = script_dir / REPORTS_DIR_NAME   # Opérateur "/" de pathlib pour assembler les chemins.
    reports_dir.mkdir(exist_ok=True)  # Crée le dossier s'il n'existe pas ; exist_ok évite l'erreur s'il existe déjà.

    # Nom du fichier de sortie.
    if args.output:
        output_filename = args.output
    else:
        # Nom par défaut : nom du projet + horodatage, pour ne pas écraser les rapports précédents.
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_filename = f"{root.name}_{timestamp}.txt"

    # Fusion du dossier des rapports et du nom de fichier.
    output_path = reports_dir / output_filename

    print(f"🔍 Analyse de : {root}")
    print(f"📝 Génération de l'arborescence...")

    # Génère l'arborescence puis le contenu, et les réunit dans une seule liste.
    all_lines = []
    all_lines.extend(generate_tree(root))
    all_lines.extend(generate_content(root))

    # Écrit le tout dans le fichier, une ligne par élément joinée par des sauts de ligne.
    print(f"💾 Écriture dans : {output_path}")
    output_path.write_text("\n".join(all_lines), encoding="utf-8")

    # Statistiques : nombre de lignes, taille approximative en Ko (en caractères, pas en octets).
    total_lines = len(all_lines)
    total_chars = sum(len(line) for line in all_lines)
    total_kb = total_chars / 1024

    print(f"✅ Terminé !")
    print(f"   - {total_lines} lignes")
    print(f"   - {total_kb:.1f} Ko")
    print(f"   - Fichier : {output_path}")

if __name__ == "__main__":
    # Ce bloc n'est exécuté que lorsque le fichier est lancé directement,
    # pas quand il est importé comme module.
    main()