#!/usr/bin/env python3
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

import sys
import os
import argparse
from pathlib import Path
from datetime import datetime

# --- Configuration ---
# Extensions de fichiers texte à inclure dans le `cat`
TEXT_EXTENSIONS = {
    ".py", ".ts", ".tsx", ".js", ".jsx", ".json", ".md", ".txt",
    ".yml", ".yaml", ".html", ".css", ".sql", ".sh", ".toml", ".ini",
    ".env", ".example", ".gitignore", ".dockerignore", ".mako",
}

# Dossiers à ignorer (volumineux et inutiles)
IGNORED_DIRS = {
    "node_modules", ".git", "__pycache__", ".venv", "venv",
    "dist", "build", ".pytest_cache", ".vite", ".next", ".cache",
    ".mypy_cache", ".ruff_cache", "coverage", ".nyc_output",
    ".idea", ".vscode", ".DS_Store", "rapports",
}

# Fichiers à ignorer (binaires ou trop volumineux)
IGNORED_FILES = {
    ".DS_Store", "package-lock.json", "yarn.lock", "pnpm-lock.yaml",
    "poetry.lock", "Pipfile.lock",
}

# Taille max d'un fichier à inclure (en Ko)
MAX_FILE_SIZE_KB = 500

# Dossier où sont stockés les rapports
REPORTS_DIR_NAME = "rapports"


def should_ignore_dir(dir_name: str) -> bool:
    """Vérifie si un dossier doit être ignoré."""
    return dir_name in IGNORED_DIRS


def should_ignore_file(file_path: Path) -> bool:
    """Vérifie si un fichier doit être ignoré."""
    if file_path.name in IGNORED_FILES:
        return True
    # Ignorer les fichiers binaires connus
    if file_path.suffix.lower() in {".png", ".jpg", ".jpeg", ".gif", ".svg", ".ico",
                                     ".pdf", ".zip", ".tar", ".gz", ".mp4", ".mp3",
                                     ".woff", ".woff2", ".ttf", ".eot", ".pyc"}:
        return True
    # Ignorer les fichiers trop volumineux
    try:
        if file_path.stat().st_size > MAX_FILE_SIZE_KB * 1024:
            return True
    except OSError:
        return True
    return False


def is_text_file(file_path: Path) -> bool:
    """Vérifie si un fichier est un fichier texte (par extension)."""
    return file_path.suffix.lower() in TEXT_EXTENSIONS or file_path.name in TEXT_EXTENSIONS


def generate_tree(root: Path) -> list[str]:
    """Génère l'arborescence du projet (comme `tree`)."""
    lines = []
    lines.append(f"# Arborescence — {root.name}")
    lines.append(f"Généré le : {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    lines.append(f"Chemin : {root}")
    lines.append("=" * 70)
    lines.append("")

    def walk(directory: Path, prefix: str = ""):
        try:
            entries = sorted(directory.iterdir(), key=lambda e: (not e.is_dir(), e.name.lower()))
        except PermissionError:
            return

        # Filtrer les dossiers et fichiers
        entries = [e for e in entries if not (e.is_dir() and should_ignore_dir(e.name))]
        entries = [e for e in entries if not (e.is_file() and should_ignore_file(e))]

        for i, entry in enumerate(entries):
            is_last = (i == len(entries) - 1)
            connector = "└── " if is_last else "├── "
            icon = "📁" if entry.is_dir() else "📄"
            lines.append(f"{prefix}{connector}{icon} {entry.name}")

            if entry.is_dir():
                extension = "    " if is_last else "│   "
                walk(entry, prefix + extension)

    walk(root)
    return lines


def generate_content(root: Path) -> list[str]:
    """Génère le contenu de tous les fichiers texte (comme `cat`)."""
    lines = []
    lines.append("")
    lines.append("=" * 70)
    lines.append("# Contenu des fichiers")
    lines.append("=" * 70)
    lines.append("")

    for file_path in sorted(root.rglob("*")):
        if not file_path.is_file():
            continue
        if should_ignore_file(file_path):
            continue
        if not is_text_file(file_path):
            continue
        # Ignorer le dossier des rapports
        if REPORTS_DIR_NAME in file_path.parts:
            continue

        rel_path = file_path.relative_to(root)
        lines.append("")
        lines.append("=" * 70)
        lines.append(f"📄 FICHIER : {rel_path}")
        lines.append("=" * 70)

        try:
            content = file_path.read_text(encoding="utf-8", errors="ignore")
            lines.append(content)
        except Exception as e:
            lines.append(f"[Erreur de lecture : {e}]")

    return lines


def main():
    parser = argparse.ArgumentParser(description="Visualiser un dépôt (tree + cat)")
    parser.add_argument("path", help="Chemin du projet à visualiser")
    parser.add_argument("--output", "-o", help="Nom du fichier de sortie (sera placé dans scripts/rapports/)")
    args = parser.parse_args()

    root = Path(args.path).expanduser().resolve()
    if not root.exists():
        print(f"❌ Le dossier '{root}' n'existe pas.")
        sys.exit(1)

    # Déterminer le dossier des rapports (à côté du script)
    script_dir = Path(__file__).parent.resolve()
    reports_dir = script_dir / REPORTS_DIR_NAME
    reports_dir.mkdir(exist_ok=True)  # Crée le dossier s'il n'existe pas

    # Nom du fichier de sortie
    if args.output:
        output_filename = args.output
    else:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_filename = f"{root.name}_{timestamp}.txt"

    output_path = reports_dir / output_filename

    print(f"🔍 Analyse de : {root}")
    print(f"📝 Génération de l'arborescence...")

    # Générer le contenu
    all_lines = []
    all_lines.extend(generate_tree(root))
    all_lines.extend(generate_content(root))

    # Écrire le fichier
    print(f"💾 Écriture dans : {output_path}")
    output_path.write_text("\n".join(all_lines), encoding="utf-8")

    # Statistiques
    total_lines = len(all_lines)
    total_chars = sum(len(line) for line in all_lines)
    total_kb = total_chars / 1024

    print(f"✅ Terminé !")
    print(f"   - {total_lines} lignes")
    print(f"   - {total_kb:.1f} Ko")
    print(f"   - Fichier : {output_path}")


if __name__ == "__main__":
    main()
