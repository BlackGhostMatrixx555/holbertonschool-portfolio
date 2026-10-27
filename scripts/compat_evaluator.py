#!/usr/bin/env python3
"""
CampOrga — Outil d'Audit Multi-Projets et de Sécurité
Usage:
    python3 compat_evaluator.py <projet1> [projet2] ...
    python3 compat_evaluator.py --full <projet1>   # Exporte aussi l'arborescence complète
"""

import sys
import re
from pathlib import Path
from datetime import datetime

# Couleurs terminal
GREEN = '\033[92m'
YELLOW = '\033[93m'
RED = '\033[91m'
BLUE = '\033[94m'
BOLD = '\033[1m'
RESET = '\033[0m'

# Contrat d'API commun
STANDARD_ROUTES = {
    "POST /api/auth/login",
    "POST /api/auth/register",
    "GET /api/camps",
    "POST /api/camps",
    "POST /api/camps/{id}/registrations",
    "POST /api/contact/chat",
}

# Extensions de fichiers texte à inclure dans l'export complet
TEXT_EXTENSIONS = {
    ".py", ".ts", ".tsx", ".js", ".jsx", ".json", ".md", ".txt",
    ".yml", ".yaml", ".html", ".css", ".sql", ".sh", ".toml", ".ini",
}

# Dossiers à ignorer dans l'export complet
IGNORED_DIRS = {
    "node_modules", ".git", "__pycache__", ".venv", "venv",
    "dist", "build", ".pytest_cache", ".vite", ".next", ".cache"
}


class ProjectAuditor:
    def __init__(self, project_path):
        self.path = Path(project_path).expanduser().resolve()
        self.project_name = self.path.name
        self.report_lines = []
        self.missing_files = []
        self.missing_routes = set(STANDARD_ROUTES)
        self.extra_routes = set()
        self.all_routes = set()
        self.git_conflicts = []
        self.dependencies = {}
        self.security_issues = []
        self.super_admins_count = 0

    def log(self, msg, level="INFO"):
        prefix = {"INFO": "🔵", "OK": "✅", "WARN": "⚠️", "ERR": "❌"}.get(level, "🔵")
        line = f"{prefix} [{level}] {msg}"
        print(line)
        self.report_lines.append(line)

    # ------------------------------------------------------------------
    # Extraction des routes
    # ------------------------------------------------------------------
    def extract_prefixes(self):
        prefixes = {}
        main_file = self.path / "backend/app/main.py"
        if not main_file.exists():
            return prefixes
        content = main_file.read_text(errors="ignore")
        matches = re.findall(
            r'app\.include_router\(\s*(\w+)\.router(?:\s*,\s*prefix\s*=\s*[\'"]([^\'"]*)[\'"])?\s*\)',
            content,
        )
        for router_name, prefix in matches:
            prefixes[router_name] = prefix or ""
        return prefixes

    def extract_routes(self):
        prefixes = self.extract_prefixes()
        found_routes = set()
        for py_file in self.path.rglob("*.py"):
            if not any(x in str(py_file) for x in ["/routes/", "/api/"]):
                continue
            try:
                content = py_file.read_text(errors="ignore")
            except Exception:
                continue

            router_name = py_file.stem
            local_prefix = ""
            local_match = re.search(
                r'APIRouter\([^)]*prefix\s*=\s*[\'"]([^\'"]*)[\'"]', content
            )
            if local_match:
                local_prefix = local_match.group(1)

            matches = re.findall(
                r'@router\.(get|post|put|patch|delete)\([\'"]([^\'"]*)[\'"]', content
            )
            for method, path in matches:
                global_prefix = prefixes.get(router_name, "")
                full_path = f"{global_prefix}{local_prefix}{path}"
                full_path = re.sub(r'/+', '/', full_path)
                full_path = re.sub(r'\{[^}]+\}', '{id}', full_path)
                if not full_path.startswith('/'):
                    full_path = '/' + full_path
                found_routes.add(f"{method.upper()} {full_path}")

        self.all_routes = found_routes
        return found_routes

    # ------------------------------------------------------------------
    # Dépendances
    # ------------------------------------------------------------------
    def check_dependencies(self):
        req_file = self.path / "backend/requirements.txt"
        if not req_file.exists():
            return
        content = req_file.read_text(errors="ignore")
        for line in content.splitlines():
            if "==" in line:
                pkg, ver = line.strip().split("==")[0], line.strip().split("==")[1]
                self.dependencies[pkg.lower()] = ver

    # ------------------------------------------------------------------
    # Conflits Git
    # ------------------------------------------------------------------
    def check_git_conflicts(self):
        conflict_pattern = re.compile(r'^(<<<<<<< |=======|>>>>>>> )', re.MULTILINE)
        for file in self.path.rglob("*"):
            if file.is_file() and file.suffix in [".py", ".ts", ".tsx", ".js", ".json", ".md"]:
                try:
                    content = file.read_text(errors="ignore")
                    if conflict_pattern.search(content):
                        self.git_conflicts.append(str(file.relative_to(self.path)))
                except Exception:
                    pass

    # ------------------------------------------------------------------
    # Sécurité
    # ------------------------------------------------------------------
    def check_security(self):
        for py_file in self.path.rglob("*.py"):
            if "test_" in py_file.name or "conftest" in py_file.name or "compat_evaluator" in py_file.name:
                continue
            try:
                content = py_file.read_text(errors="ignore")
            except Exception:
                continue

            # Création réelle de Super Admin
            creation_patterns = [
                r'UserService\([^)]*\)\.create\([\s\S]*?SUPER_ADMIN',
                r'User\([\s\S]*?role\s*=\s*UserRole\.SUPER_ADMIN',
                r'role\s*=\s*[\'"]super_admin[\'"]',
            ]
            for pattern in creation_patterns:
                if re.search(pattern, content, re.DOTALL):
                    self.super_admins_count += 1
                    self.log(f"Création de Super Admin dans {py_file.name}", "WARN")
                    break

            # Failles dans les fichiers de config/route uniquement
            is_config_or_route = any(
                x in str(py_file) for x in ["/routes/", "/api/", "main.py", "config.py", "security.py"]
            )
            if is_config_or_route:
                if "SECRET_KEY = " in content and "os.getenv" not in content and "settings.secret_key" not in content:
                    self.security_issues.append(f"Clé secrète en dur dans {py_file.name}")
                if "allow_origins=['*']" in content or 'allow_origins=["*"]' in content:
                    self.security_issues.append(f"CORS permissif dans {py_file.name}")
                if "debug=True" in content.lower():
                    self.security_issues.append(f"DEBUG activé dans {py_file.name}")

        if self.super_admins_count > 1:
            self.security_issues.append(
                f"⚠️ {self.super_admins_count} créations de SUPER_ADMIN détectées."
            )
        elif self.super_admins_count == 1:
            self.log("1 création de Super Admin trouvée (normal).", "OK")
        else:
            self.log("Aucune création de Super Admin détectée.", "INFO")

    # ------------------------------------------------------------------
    # Analyse complète
    # ------------------------------------------------------------------
    def analyze(self):
        print(f"\n{BLUE}=== Audit : {self.project_name} ==={RESET}")
        self.log(f"Dossier : {self.path}", "INFO")

        if not self.path.exists():
            self.log("Le dossier n'existe pas.", "ERR")
            return

        for f in ["backend/app/main.py", "backend/app/models/", "backend/tests/", "backend/requirements.txt"]:
            if not (self.path / f).exists():
                self.missing_files.append(f)
                self.log(f"Manquant : {f}", "WARN")
            else:
                self.log(f"Trouvé : {f}", "OK")

        found_routes = self.extract_routes()
        self.log(f"{len(found_routes)} routes détectées au total", "INFO")
        for route in found_routes:
            if route in self.missing_routes:
                self.missing_routes.remove(route)
                self.log(f"Route compatible : {route}", "OK")
            else:
                self.extra_routes.add(route)

        self.check_dependencies()
        self.log(f"{len(self.dependencies)} dépendances analysées", "INFO")

        self.check_git_conflicts()
        if self.git_conflicts:
            self.log(f"⚠️ {len(self.git_conflicts)} fichiers avec des conflits Git !", "ERR")

        self.log("Analyse de sécurité en cours...", "INFO")
        self.check_security()
        for issue in self.security_issues:
            self.log(issue, "ERR")

    def get_score(self):
        score = 100
        score -= len(self.missing_files) * 10
        score -= len(self.missing_routes) * 10
        score -= len(self.git_conflicts) * 5
        score -= len(self.security_issues) * 15
        return max(0, score)

    # ------------------------------------------------------------------
    # Export complet de l'arborescence
    # ------------------------------------------------------------------
    def export_full_tree(self, output_path: Path):
        """Exporte l'arborescence et le contenu des fichiers texte."""
        with open(output_path, "w", encoding="utf-8") as out:
            out.write(f"# Arborescence complète — {self.project_name}\n")
            out.write(f"Généré le : {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
            out.write(f"Chemin : {self.path}\n\n")
            out.write("=" * 70 + "\n\n")

            # 1. Arborescence
            out.write("## 📁 Structure des fichiers\n\n")
            for file in sorted(self.path.rglob("*")):
                if any(part in IGNORED_DIRS for part in file.parts):
                    continue
                rel = file.relative_to(self.path)
                indent = "  " * (len(rel.parts) - 1)
                symbol = "📁" if file.is_dir() else "📄"
                out.write(f"{indent}{symbol} {rel.name}\n")
            out.write("\n" + "=" * 70 + "\n\n")

            # 2. Contenu des fichiers texte
            out.write("## 📄 Contenu des fichiers\n\n")
            for file in sorted(self.path.rglob("*")):
                if any(part in IGNORED_DIRS for part in file.parts):
                    continue
                if not file.is_file():
                    continue
                if file.suffix.lower() not in TEXT_EXTENSIONS:
                    continue

                rel = file.relative_to(self.path)
                out.write("\n" + "=" * 70 + "\n")
                out.write(f"📄 FICHIER : {rel}\n")
                out.write("=" * 70 + "\n")
                try:
                    out.write(file.read_text(errors="ignore"))
                except Exception as e:
                    out.write(f"[Erreur de lecture : {e}]")
                out.write("\n")

        print(f"{BLUE}✅ Arborescence complète :{RESET} {GREEN}{output_path}{RESET}")


# ----------------------------------------------------------------------
# Comparaison des dépendances
# ----------------------------------------------------------------------
def compare_dependencies(auditors):
    print(f"\n{BLUE}=== Comparaison des dépendances ==={RESET}")
    all_pkgs = set()
    for aud in auditors:
        all_pkgs.update(aud.dependencies.keys())

    found_diff = False
    for pkg in sorted(all_pkgs):
        versions = {aud.project_name: aud.dependencies.get(pkg) for aud in auditors if pkg in aud.dependencies}
        if len(set(versions.values())) > 1:
            found_diff = True
            print(f"{YELLOW}⚠️  Conflit de version pour '{pkg}' :{RESET}")
            for proj, ver in versions.items():
                print(f"   - {proj} : {ver}")

    if not found_diff:
        print(f"{GREEN}✅ Aucun conflit de version détecté.{RESET}")


# ----------------------------------------------------------------------
# Résumé final
# ----------------------------------------------------------------------
def print_global_summary(auditors):
    print("\n" + "=" * 70)
    print(f"{BOLD}{BLUE}📋 RÉSUMÉ FINAL DE L'AUDIT GLOBAL{RESET}")
    print("=" * 70)

    print(f"\n{BOLD}{'Projet':<35} {'Score':<8} {'SuperAdmins':<12} {'Sécurité':<10}{RESET}")
    print("-" * 70)
    for aud in auditors:
        sec = "❌ Failles" if aud.security_issues else "✅ OK"
        print(f"{aud.project_name:<35} {aud.get_score():>3}/100   {aud.super_admins_count:<12} {sec}")
    print("-" * 70)

    for aud in auditors:
        print(f"\n{BOLD}📦 {aud.project_name}{RESET} — Score : {aud.get_score()}/100")
        if aud.security_issues:
            print(f"   {RED}🚨 FAILLES :{RESET}")
            for issue in aud.security_issues:
                print(f"   {RED}   → {issue}{RESET}")
        if aud.git_conflicts:
            print(f"   {RED}🚨 CONFLITS GIT :{RESET}")
            for c in aud.git_conflicts:
                print(f"   {RED}   → {c}{RESET}")
        if aud.missing_routes:
            print(f"   {RED}🚨 Routes manquantes :{RESET}")
            for r in sorted(aud.missing_routes):
                print(f"   {RED}   → {r}{RESET}")
        if not aud.security_issues and not aud.git_conflicts and not aud.missing_routes and not aud.missing_files:
            print(f"   {GREEN}🎉 Projet parfait !{RESET}")

    total_score = sum(a.get_score() for a in auditors) / len(auditors)
    print("\n" + "=" * 70)
    print(f"{BOLD}🎯 SCORE GLOBAL : {total_score:.1f}/100{RESET}")
    print("=" * 70 + "\n")


# ----------------------------------------------------------------------
# Génération des rapports Markdown
# ----------------------------------------------------------------------
def generate_reports(auditors):
    script_dir = Path(__file__).parent.resolve()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M")

    for aud in auditors:
        safe_name = re.sub(r"[^\w\-]", "_", aud.project_name)
        report_path = script_dir / f"RAPPORT_{safe_name}_{timestamp}.md"

        with open(report_path, "w", encoding="utf-8") as f:
            f.write(f"# Rapport d'Audit — {aud.project_name}\n\n")
            f.write(f"**Score :** {aud.get_score()}/100\n")
            f.write(f"**Super Admins :** {aud.super_admins_count}\n\n")

            if aud.security_issues:
                f.write("## 🚨 Failles de Sécurité\n\n")
                for issue in aud.security_issues:
                    f.write(f"- `{issue}`\n")
                f.write("\n")

            if aud.git_conflicts:
                f.write("## 🚨 Conflits Git\n\n")
                for c in aud.git_conflicts:
                    f.write(f"- `{c}`\n")
                f.write("\n")

            if aud.missing_routes:
                f.write("## ❌ Routes manquantes\n\n")
                for r in sorted(aud.missing_routes):
                    f.write(f"- `{r}`\n")
                f.write("\n")

            f.write("## ✅ Routes détectées\n\n")
            for r in sorted(aud.all_routes):
                f.write(f"- `{r}`\n")

        print(f"{BLUE}✅ Rapport :{RESET} {GREEN}{report_path}{RESET}")


if __name__ == "__main__":
    args = sys.argv[1:]
    full_mode = "--full" in args
    if full_mode:
        args.remove("--full")

    if not args:
        print(f"Usage: python3 {sys.argv[0]} [--full] <projet1> [projet2] ...")
        sys.exit(1)

    auditors = []
    for path in args:
        aud = ProjectAuditor(path)
        aud.analyze()
        auditors.append(aud)

        if full_mode:
            script_dir = Path(__file__).parent.resolve()
            safe_name = re.sub(r"[^\w\-]", "_", aud.project_name)
            export_path = script_dir / f"ARBORESCENCE_{safe_name}.txt"
            aud.export_full_tree(export_path)

    compare_dependencies(auditors)
    generate_reports(auditors)
    print_global_summary(auditors)
