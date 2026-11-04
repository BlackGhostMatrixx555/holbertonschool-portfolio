#!/usr/bin/env python3
# Indique à Linux/macOS d'exécuter ce fichier avec l'interpréteur Python 3 trouvé dans le PATH
"""
CampOrga — Outil d'Audit Multi-Projets et de Sécurité
Usage:
    python3 compat_evaluator.py <projet1> [projet2] ...
    python3 compat_evaluator.py --full <projet1>   # Exporte aussi l'arborescence complète
"""
# Docstring : description du script et exemples d'utilisation en ligne de commande

import sys  # Module pour lire les arguments passés au script (sys.argv) et quitter le programme
import re  # Module des expressions régulières, utilisé pour chercher des motifs dans le code
from pathlib import Path  # Classe pour manipuler les chemins de fichiers et dossiers de façon orientée objet
from datetime import datetime  # Classe pour obtenir la date et l'heure actuelles (horodatage des rapports)

# Couleurs terminal
GREEN = '\033[92m'  # Code ANSI pour afficher du texte en vert dans le terminal
YELLOW = '\033[93m'  # Code ANSI pour afficher du texte en jaune
RED = '\033[91m'  # Code ANSI pour afficher du texte en rouge
BLUE = '\033[94m'  # Code ANSI pour afficher du texte en bleu
BOLD = '\033[1m'  # Code ANSI pour mettre le texte en gras
RESET = '\033[0m'  # Code ANSI pour remettre la couleur et le style par défaut

# Contrat d'API commun
STANDARD_ROUTES = {  # Ensemble (set) des routes que chaque projet doit obligatoirement exposer
    "POST /api/auth/login",  # Route de connexion d'un utilisateur
    "POST /api/auth/register",  # Route d'inscription d'un nouvel utilisateur
    "GET /api/camps",  # Route de récupération de la liste des camps
    "POST /api/camps",  # Route de création d'un camp
    "POST /api/camps/{id}/registrations",  # Route d'inscription d'un participant à un camp donné
    "POST /api/contact/chat",  # Route du chat de contact
}  # Fin de l'ensemble des routes standard

# Extensions de fichiers texte à inclure dans l'export complet
TEXT_EXTENSIONS = {  # Ensemble des extensions considérées comme du texte lisible
    ".py", ".ts", ".tsx", ".js", ".jsx", ".json", ".md", ".txt",  # Code Python, TypeScript, JavaScript et documentation
    ".yml", ".yaml", ".html", ".css", ".sql", ".sh", ".toml", ".ini",  # Fichiers de config, web et scripts
}  # Fin de l'ensemble des extensions

# Dossiers à ignorer dans l'export complet
IGNORED_DIRS = {  # Ensemble des dossiers à exclure car générés automatiquement ou non pertinents
    "node_modules", ".git", "__pycache__", ".venv", "venv",  # Dépendances JS, historique Git, cache Python, environnements virtuels
    "dist", "build", ".pytest_cache", ".vite", ".next", ".cache"  # Dossiers de build et de cache des outils
}  # Fin de l'ensemble des dossiers ignorés

class ProjectAuditor:  # Classe qui regroupe toute l'analyse d'un projet
    def __init__(self, project_path):  # Constructeur appelé à la création d'un auditeur pour un projet donné
        self.path = Path(project_path).expanduser().resolve()  # Convertit le chemin reçu en chemin absolu (gère le ~ et les liens)
        self.project_name = self.path.name  # Récupère le nom du dossier du projet
        self.report_lines = []  # Liste qui stocke toutes les lignes de messages affichées
        self.missing_files = []  # Liste des fichiers ou dossiers attendus mais absents
        self.missing_routes = set(STANDARD_ROUTES)  # Copie des routes standard ; on retirera celles trouvées dans le projet
        self.extra_routes = set()  # Ensemble des routes présentes dans le projet mais absentes du contrat standard
        self.all_routes = set()  # Ensemble de toutes les routes détectées dans le projet
        self.git_conflicts = []  # Liste des fichiers contenant des marqueurs de conflit Git
        self.dependencies = {}  # Dictionnaire {nom_du_paquet: version} lu depuis requirements.txt
        self.security_issues = []  # Liste des problèmes de sécurité détectés
        self.super_admins_count = 0  # Compteur du nombre de fichiers créant un Super Admin

    def log(self, msg, level="INFO"):  # Méthode qui affiche et enregistre un message avec un niveau de gravité
        prefix = {"INFO": "🔵", "OK": "✅", "WARN": "⚠️", "ERR": "❌"}.get(level, "🔵")  # Choisit l'icône selon le niveau, bleu par défaut
        line = f"{prefix} [{level}] {msg}"  # Construit la ligne complète à afficher
        print(line)  # Affiche la ligne dans le terminal
        self.report_lines.append(line)  # Ajoute la ligne à l'historique du rapport

    # ------------------------------------------------------------------
    # Extraction des routes
    # ------------------------------------------------------------------
    def extract_prefixes(self):  # Méthode qui lit main.py pour trouver les préfixes donnés à chaque routeur
        prefixes = {}  # Dictionnaire {nom_du_routeur: préfixe} vide au départ
        main_file = self.path / "backend/app/main.py"  # Construit le chemin vers le fichier principal de l'application
        if not main_file.exists():  # Si le fichier n'existe pas
            return prefixes  # On renvoie un dictionnaire vide
        content = main_file.read_text(errors="ignore")  # Lit le contenu du fichier en ignorant les caractères illisibles
        matches = re.findall(  # Cherche tous les appels app.include_router(...) avec leur éventuel préfixe
            r'app\.include_router\(\s*(\w+)\.router(?:\s*,\s*prefix\s*=\s*[\'"]([^\'"]*)[\'"])?\s*\)',  # Motif regex décrivant l'appel
            content,  # Texte dans lequel chercher
        )  # Fin de la recherche
        for router_name, prefix in matches:  # Parcourt chaque couple (nom du routeur, préfixe) trouvé
            prefixes[router_name] = prefix or ""  # Enregistre le préfixe, ou une chaîne vide si aucun préfixe n'est défini
        return prefixes  # Renvoie le dictionnaire des préfixes

    def extract_routes(self):  # Méthode qui parcourt les fichiers Python pour reconstruire les routes complètes
        prefixes = self.extract_prefixes()  # Récupère d'abord les préfixes globaux définis dans main.py
        found_routes = set()  # Ensemble qui va contenir les routes trouvées
        for py_file in self.path.rglob("*.py"):  # Parcourt récursivement tous les fichiers .py du projet
            if not any(x in str(py_file) for x in ["/routes/", "/api/"]):  # Ignore les fichiers qui ne sont pas dans un dossier routes ou api
                continue  # Passe au fichier suivant
            try:  # Début d'un bloc protégé contre les erreurs de lecture
                content = py_file.read_text(errors="ignore")  # Lit le contenu du fichier
            except Exception:  # En cas d'erreur quelconque de lecture
                continue  # On ignore ce fichier et on passe au suivant

            router_name = py_file.stem  # Nom du fichier sans extension, utilisé comme nom de routeur
            local_prefix = ""  # Préfixe local, vide par défaut
            local_match = re.search(  # Cherche un préfixe déclaré directement dans APIRouter(...)
                r'APIRouter\([^)]*prefix\s*=\s*[\'"]([^\'"]*)[\'"]', content  # Motif regex du préfixe local
            )  # Fin de la recherche
            if local_match:  # Si un préfixe local a été trouvé
                local_prefix = local_match.group(1)  # On récupère la valeur du préfixe

            matches = re.findall(  # Cherche toutes les décorations de route (@router.get, @router.post, etc.)
                r'@router\.(get|post|put|patch|delete)\([\'"]([^\'"]*)[\'"]', content  # Motif regex : méthode HTTP et chemin
            )  # Fin de la recherche
            for method, path in matches:  # Parcourt chaque couple (méthode HTTP, chemin) trouvé
                global_prefix = prefixes.get(router_name, "")  # Récupère le préfixe global du routeur, vide si absent
                full_path = f"{global_prefix}{local_prefix}{path}"  # Assemble préfixe global, préfixe local et chemin
                full_path = re.sub(r'/+', '/', full_path)  # Remplace les doubles slashes (//) par un seul slash
                full_path = re.sub(r'\{[^}]+\}', '{id}', full_path)  # Uniformise tous les paramètres {xxx} en {id}
                if not full_path.startswith('/'):  # Si le chemin ne commence pas par un slash
                    full_path = '/' + full_path  # On en ajoute un au début
                found_routes.add(f"{method.upper()} {full_path}")  # Ajoute la route au format "MÉTHODE /chemin" en majuscules
        self.all_routes = found_routes  # Sauvegarde toutes les routes trouvées dans l'attribut de l'objet
        return found_routes  # Renvoie l'ensemble des routes

    # ------------------------------------------------------------------
    # Dépendances
    # ------------------------------------------------------------------
    def check_dependencies(self):  # Méthode qui lit le fichier requirements.txt
        req_file = self.path / "backend/requirements.txt"  # Chemin vers le fichier des dépendances Python
        if not req_file.exists():  # Si le fichier est absent
            return  # On arrête la méthode sans rien faire
        content = req_file.read_text(errors="ignore")  # Lit le contenu du fichier
        for line in content.splitlines():  # Parcourt le fichier ligne par ligne
            if "==" in line:  # Ne garde que les lignes qui fixent une version exacte (ex : fastapi==0.100.0)
                pkg, ver = line.strip().split("==")[0], line.strip().split("==")[1]  # Sépare le nom du paquet et sa version
                self.dependencies[pkg.lower()] = ver  # Enregistre le paquet en minuscules avec sa version

    # ------------------------------------------------------------------
    # Conflits Git
    # ------------------------------------------------------------------
    def check_git_conflicts(self):  # Méthode qui cherche les marqueurs de conflit Git dans les fichiers
        conflict_pattern = re.compile(r'^(<<<<<<< |=======|>>>>>>> )', re.MULTILINE)  # Motif qui repère les marqueurs en début de ligne
        for file in self.path.rglob("*"):  # Parcourt tous les fichiers et dossiers du projet
            if file.is_file() and file.suffix in [".py", ".ts", ".tsx", ".js", ".json", ".md"]:  # Ne garde que les fichiers de code et de doc
                try:  # Bloc protégé contre les erreurs de lecture
                    content = file.read_text(errors="ignore")  # Lit le contenu du fichier
                    if conflict_pattern.search(content):  # Si un marqueur de conflit est trouvé
                        self.git_conflicts.append(str(file.relative_to(self.path)))  # Ajoute le chemin relatif à la liste
                except Exception:  # En cas d'erreur de lecture
                    pass  # On ignore simplement ce fichier

    # ------------------------------------------------------------------
    # Sécurité
    # ------------------------------------------------------------------
    def check_security(self):  # Méthode qui recherche des motifs dangereux dans le code
        for py_file in self.path.rglob("*.py"):  # Parcourt tous les fichiers Python du projet
            if "test_" in py_file.name or "conftest" in py_file.name or "compat_evaluator" in py_file.name:  # Ignore les fichiers de test et ce script lui-même
                continue  # Passe au fichier suivant
            try:  # Bloc protégé contre les erreurs de lecture
                content = py_file.read_text(errors="ignore")  # Lit le contenu du fichier
            except Exception:  # En cas d'erreur de lecture
                continue  # On passe au fichier suivant

            # Création réelle de Super Admin
            creation_patterns = [  # Liste des motifs regex qui signalent la création d'un Super Admin
                r'UserService\([^)]*\)\.create\([\s\S]*?SUPER_ADMIN',  # Appel à un service de création avec le rôle SUPER_ADMIN
                r'User\([\s\S]*?role\s*=\s*UserRole\.SUPER_ADMIN',  # Instanciation d'un User avec le rôle SUPER_ADMIN
                r'role\s*=\s*[\'"]super_admin[\'"]',  # Rôle défini directement par une chaîne 'super_admin'
            ]  # Fin de la liste des motifs
            for pattern in creation_patterns:  # Teste chaque motif l'un après l'autre
                if re.search(pattern, content, re.DOTALL):  # Cherche le motif dans le contenu, en incluant les retours à la ligne
                    self.super_admins_count += 1  # Incrémente le compteur de créations de Super Admin
                    self.log(f"Création de Super Admin dans {py_file.name}", "WARN")  # Affiche un avertissement
                    break  # Inutile de tester les autres motifs pour ce fichier

            # Failles dans les fichiers de config/route uniquement
            is_config_or_route = any(  # Vrai si le fichier fait partie des routes ou de la configuration
                x in str(py_file) for x in ["/routes/", "/api/", "main.py", "config.py", "security.py"]  # Liste des noms ou dossiers concernés
            )  # Fin du test
            if is_config_or_route:  # Si le fichier est concerné, on cherche les failles
                if "SECRET_KEY = " in content and "os.getenv" not in content and "settings.secret_key" not in content:  # Clé secrète écrite en dur, sans lecture depuis l'environnement
                    self.security_issues.append(f"Clé secrète en dur dans {py_file.name}")  # Enregistre la faille
                if "allow_origins=['*']" in content or 'allow_origins=["*"]' in content:  # CORS ouvert à toutes les origines
                    self.security_issues.append(f"CORS permissif dans {py_file.name}")  # Enregistre la faille
                if "debug=True" in content.lower():  # Mode debug activé
                    self.security_issues.append(f"DEBUG activé dans {py_file.name}")  # Enregistre la faille

        if self.super_admins_count > 1:  # Plus d'un endroit crée un Super Admin
            self.security_issues.append(  # Ajoute un problème à la liste
                f"⚠️ {self.super_admins_count} créations de SUPER_ADMIN détectées."  # Message décrivant le problème
            )  # Fin de l'ajout
        elif self.super_admins_count == 1:  # Exactement une création, cas attendu
            self.log("1 création de Super Admin trouvée (normal).", "OK")  # Message de confirmation
        else:  # Aucune création trouvée
            self.log("Aucune création de Super Admin détectée.", "INFO")  # Message informatif

    # ------------------------------------------------------------------
    # Analyse complète
    # ------------------------------------------------------------------
    def analyze(self):  # Méthode principale qui lance toutes les vérifications dans l'ordre
        print(f"\n{BLUE}=== Audit : {self.project_name} ==={RESET}")  # Affiche le titre de l'audit en bleu
        self.log(f"Dossier : {self.path}", "INFO")  # Affiche le chemin du projet analysé

        if not self.path.exists():  # Si le dossier du projet n'existe pas
            self.log("Le dossier n'existe pas.", "ERR")  # Signale l'erreur
            return  # Arrête l'analyse de ce projet

        for f in ["backend/app/main.py", "backend/app/models/", "backend/tests/", "backend/requirements.txt"]:  # Liste des éléments indispensables
            if not (self.path / f).exists():  # Si l'élément est absent
                self.missing_files.append(f)  # Il est ajouté à la liste des manquants
                self.log(f"Manquant : {f}", "WARN")  # Avertissement affiché
            else:  # Sinon l'élément est présent
                self.log(f"Trouvé : {f}", "OK")  # Confirmation affichée

        found_routes = self.extract_routes()  # Lance l'extraction des routes du projet
        self.log(f"{len(found_routes)} routes détectées au total", "INFO")  # Affiche le nombre de routes trouvées
        for route in found_routes:  # Parcourt chaque route trouvée
            if route in self.missing_routes:  # Si la route fait partie du contrat standard
                self.missing_routes.remove(route)  # On la retire de la liste des routes manquantes
                self.log(f"Route compatible : {route}", "OK")  # Confirme sa présence
            else:  # Sinon la route n'est pas dans le contrat
                self.extra_routes.add(route)  # On la range dans les routes en plus

        self.check_dependencies()  # Lit les dépendances du projet
        self.log(f"{len(self.dependencies)} dépendances analysées", "INFO")  # Affiche le nombre de dépendances lues

        self.check_git_conflicts()  # Recherche les conflits Git
        if self.git_conflicts:  # Si au moins un fichier est en conflit
            self.log(f"⚠️ {len(self.git_conflicts)} fichiers avec des conflits Git !", "ERR")  # Affiche l'erreur

        self.log("Analyse de sécurité en cours...", "INFO")  # Indique le début de l'analyse de sécurité
        self.check_security()  # Lance la recherche de failles
        for issue in self.security_issues:  # Affiche chaque faille trouvée
            self.log(issue, "ERR")  # Avec le niveau erreur

    def get_score(self):  # Méthode qui calcule une note sur 100 pour le projet
        score = 100  # On part d'un score parfait
        score -= len(self.missing_files) * 10  # Retire 10 points par fichier manquant
        score -= len(self.missing_routes) * 10  # Retire 10 points par route standard absente
        score -= len(self.git_conflicts) * 5  # Retire 5 points par fichier en conflit Git
        score -= len(self.security_issues) * 15  # Retire 15 points par faille de sécurité
        return max(0, score)  # Renvoie le score, sans jamais descendre sous 0

    # ------------------------------------------------------------------
    # Export complet de l'arborescence
    # ------------------------------------------------------------------
    def export_full_tree(self, output_path: Path):  # Méthode qui écrit l'arborescence et le contenu des fichiers dans un fichier texte
        """Exporte l'arborescence et le contenu des fichiers texte."""  # Docstring décrivant la méthode
        with open(output_path, "w", encoding="utf-8") as out:  # Ouvre le fichier de sortie en écriture avec encodage UTF-8
            out.write(f"# Arborescence complète — {self.project_name}\n")  # Écrit le titre du rapport
            out.write(f"Généré le : {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")  # Écrit la date et l'heure de génération
            out.write(f"Chemin : {self.path}\n\n")  # Écrit le chemin absolu du projet
            out.write("=" * 70 + "\n\n")  # Écrit une ligne de séparation

            # 1. Arborescence
            out.write("## 📁 Structure des fichiers\n\n")  # Titre de la section arborescence
            for file in sorted(self.path.rglob("*")):  # Parcourt tous les éléments du projet, triés par nom
                if any(part in IGNORED_DIRS for part in file.parts):  # Si un segment du chemin est un dossier ignoré
                    continue  # On saute cet élément
                rel = file.relative_to(self.path)  # Chemin relatif à la racine du projet
                indent = "  " * (len(rel.parts) - 1)  # Indentation proportionnelle à la profondeur
                symbol = "📁" if file.is_dir() else "📄"  # Icône dossier ou fichier
                out.write(f"{indent}{symbol} {rel.name}\n")  # Écrit la ligne de l'arborescence
            out.write("\n" + "=" * 70 + "\n\n")  # Écrit une ligne de séparation

            # 2. Contenu des fichiers texte
            out.write("## 📄 Contenu des fichiers\n\n")  # Titre de la section contenu
            for file in sorted(self.path.rglob("*")):  # Reparcourt tous les éléments du projet
                if any(part in IGNORED_DIRS for part in file.parts):  # Ignore les dossiers exclus
                    continue  # Passe à l'élément suivant
                if not file.is_file():  # Ignore tout ce qui n'est pas un fichier (dossiers)
                    continue  # Passe à l'élément suivant
                if file.suffix.lower() not in TEXT_EXTENSIONS:  # Ignore les fichiers dont l'extension n'est pas textuelle
                    continue  # Passe à l'élément suivant

                rel = file.relative_to(self.path)  # Chemin relatif du fichier
                out.write("\n" + "=" * 70 + "\n")  # Ligne de séparation avant le fichier
                out.write(f"📄 FICHIER : {rel}\n")  # Nom du fichier affiché
                out.write("=" * 70 + "\n")  # Ligne de séparation après le nom
                try:  # Bloc protégé contre les erreurs de lecture
                    out.write(file.read_text(errors="ignore"))  # Écrit le contenu du fichier
                except Exception as e:  # En cas d'erreur
                    out.write(f"[Erreur de lecture : {e}]")  # Écrit le message d'erreur à la place du contenu
                out.write("\n")  # Saut de ligne final

        print(f"{BLUE}✅ Arborescence complète :{RESET} {GREEN}{output_path}{RESET}")  # Affiche le chemin du fichier créé

# ----------------------------------------------------------------------
# Comparaison des dépendances
# ----------------------------------------------------------------------
def compare_dependencies(auditors):  # Fonction qui compare les versions des paquets entre tous les projets audités
    print(f"\n{BLUE}=== Comparaison des dépendances ==={RESET}")  # Titre de la section
    all_pkgs = set()  # Ensemble de tous les noms de paquets rencontrés
    for aud in auditors:  # Parcourt chaque projet audité
        all_pkgs.update(aud.dependencies.keys())  # Ajoute les noms de paquets du projet à l'ensemble

    found_diff = False  # Indicateur : aucun conflit trouvé pour l'instant
    for pkg in sorted(all_pkgs):  # Parcourt chaque paquet, trié par ordre alphabétique
        versions = {aud.project_name: aud.dependencies.get(pkg) for aud in auditors if pkg in aud.dependencies}  # Dictionnaire {projet: version} pour ce paquet
        if len(set(versions.values())) > 1:  # Si les versions trouvées ne sont pas identiques
            found_diff = True  # Un conflit a été trouvé
            print(f"{YELLOW}⚠️  Conflit de version pour '{pkg}' :{RESET}")  # Affiche le nom du paquet en conflit
            for proj, ver in versions.items():  # Parcourt chaque projet et sa version
                print(f"   - {proj} : {ver}")  # Affiche le projet et sa version
    if not found_diff:  # Si aucun conflit n'a été trouvé
        print(f"{GREEN}✅ Aucun conflit de version détecté.{RESET}")  # Message de confirmation

# ----------------------------------------------------------------------
# Résumé final
# ----------------------------------------------------------------------
def print_global_summary(auditors):  # Fonction qui affiche le bilan de tous les audits
    print("\n" + "=" * 70)  # Ligne de séparation
    print(f"{BOLD}{BLUE}📋 RÉSUMÉ FINAL DE L'AUDIT GLOBAL{RESET}")  # Titre du bilan
    print("=" * 70)  # Ligne de séparation

    print(f"\n{BOLD}{'Projet':<35} {'Score':<8} {'SuperAdmins':<12} {'Sécurité':<10}{RESET}")  # En-tête du tableau
    print("-" * 70)  # Ligne de séparation du tableau
    for aud in auditors:  # Parcourt chaque projet pour remplir le tableau
        sec = "❌ Failles" if aud.security_issues else "✅ OK"  # Statut de sécurité selon la présence de failles
        print(f"{aud.project_name:<35} {aud.get_score():>3}/100   {aud.super_admins_count:<12} {sec}")  # Ligne du tableau pour ce projet
    print("-" * 70)  # Ligne de séparation de fin de tableau

    for aud in auditors:  # Parcourt chaque projet pour le détail
        print(f"\n{BOLD}📦 {aud.project_name}{RESET} — Score : {aud.get_score()}/100")  # Nom et score du projet
        if aud.security_issues:  # S'il y a des failles
            print(f"   {RED}🚨 FAILLES :{RESET}")  # Titre de la section failles
            for issue in aud.security_issues:  # Parcourt chaque faille
                print(f"   {RED}   → {issue}{RESET}")  # Affiche la faille en rouge
        if aud.git_conflicts:  # S'il y a des conflits Git
            print(f"   {RED}🚨 CONFLITS GIT :{RESET}")  # Titre de la section conflits
            for c in aud.git_conflicts:  # Parcourt chaque fichier en conflit
                print(f"   {RED}   → {c}{RESET}")  # Affiche le fichier en rouge
        if aud.missing_routes:  # S'il manque des routes standard
            print(f"   {RED}🚨 Routes manquantes :{RESET}")  # Titre de la section routes
            for r in sorted(aud.missing_routes):  # Parcourt les routes manquantes triées
                print(f"   {RED}   → {r}{RESET}")  # Affiche la route en rouge
        if not aud.security_issues and not aud.git_conflicts and not aud.missing_routes and not aud.missing_files:  # Aucun problème détecté
            print(f"   {GREEN}🎉 Projet parfait !{RESET}")  # Message de félicitations

    total_score = sum(a.get_score() for a in auditors) / len(auditors)  # Calcule la moyenne des scores de tous les projets
    print("\n" + "=" * 70)  # Ligne de séparation
    print(f"{BOLD}🎯 SCORE GLOBAL : {total_score:.1f}/100{RESET}")  # Affiche la moyenne avec une décimale
    print("=" * 70 + "\n")  # Ligne de séparation finale

# ----------------------------------------------------------------------
# Génération des rapports Markdown
# ----------------------------------------------------------------------
def generate_reports(auditors):  # Fonction qui écrit un rapport Markdown pour chaque projet
    script_dir = Path(__file__).parent.resolve()  # Dossier contenant ce script, où seront créés les rapports
    timestamp = datetime.now().strftime("%Y%m%d_%H%M")  # Horodatage au format AAAAMMJJ_HHMM pour nommer les fichiers

    for aud in auditors:  # Parcourt chaque projet audité
        safe_name = re.sub(r"[^\w\-]", "_", aud.project_name)  # Remplace les caractères spéciaux du nom par des underscores
        report_path = script_dir / f"RAPPORT_{safe_name}_{timestamp}.md"  # Construit le chemin du rapport Markdown

        with open(report_path, "w", encoding="utf-8") as f:  # Ouvre le rapport en écriture UTF-8
            f.write(f"# Rapport d'Audit — {aud.project_name}\n\n")  # Titre du rapport
            f.write(f"**Score :** {aud.get_score()}/100\n")  # Écrit le score
            f.write(f"**Super Admins :** {aud.super_admins_count}\n\n")  # Écrit le nombre de Super Admins

            if aud.security_issues:  # Si des failles ont été trouvées
                f.write("## 🚨 Failles de Sécurité\n\n")  # Titre de la section
                for issue in aud.security_issues:  # Parcourt chaque faille
                    f.write(f"- `{issue}`\n")  # Écrit la faille en liste
                f.write("\n")  # Ligne vide après la section

            if aud.git_conflicts:  # Si des conflits Git existent
                f.write("## 🚨 Conflits Git\n\n")  # Titre de la section
                for c in aud.git_conflicts:  # Parcourt chaque fichier en conflit
                    f.write(f"- `{c}`\n")  # Écrit le fichier en liste
                f.write("\n")  # Ligne vide après la section

            if aud.missing_routes:  # Si des routes standard manquent
                f.write("## ❌ Routes manquantes\n\n")  # Titre de la section
                for r in sorted(aud.missing_routes):  # Parcourt les routes manquantes triées
                    f.write(f"- `{r}`\n")  # Écrit la route en liste
                f.write("\n")  # Ligne vide après la section

            f.write("## ✅ Routes détectées\n\n")  # Titre de la section des routes trouvées
            for r in sorted(aud.all_routes):  # Parcourt toutes les routes détectées triées
                f.write(f"- `{r}`\n")  # Écrit chaque route en liste

        print(f"{BLUE}✅ Rapport :{RESET} {GREEN}{report_path}{RESET}")  # Affiche le chemin du rapport créé

if __name__ == "__main__":  # Vrai uniquement si le script est lancé directement (et non importé)
    args = sys.argv[1:]  # Récupère les arguments de la ligne de commande, sans le nom du script
    full_mode = "--full" in args  # Vrai si l'option --full est présente
    if full_mode:  # Si l'option est présente
        args.remove("--full")  # On la retire de la liste pour ne garder que les chemins de projets

    if not args:  # Si aucun projet n'a été fourni
        print(f"Usage: python3 {sys.argv[0]} [--full] <projet1> [projet2] ...")  # Affiche le mode d'emploi
        sys.exit(1)  # Quitte le programme avec un code d'erreur

    auditors = []  # Liste qui va contenir un auditeur par projet
    for path in args:  # Parcourt chaque chemin de projet fourni
        aud = ProjectAuditor(path)  # Crée un auditeur pour ce projet
        aud.analyze()  # Lance l'analyse complète
        auditors.append(aud)  # Ajoute l'auditeur à la liste

        if full_mode:  # Si l'export complet est demandé
            script_dir = Path(__file__).parent.resolve()  # Dossier du script, où sera créé le fichier
            safe_name = re.sub(r"[^\w\-]", "_", aud.project_name)  # Nom du projet nettoyé pour le nom de fichier
            export_path = script_dir / f"ARBORESCENCE_{safe_name}.txt"  # Chemin du fichier d'export
            aud.export_full_tree(export_path)  # Écrit l'arborescence et le contenu dans ce fichier

    compare_dependencies(auditors)  # Compare les dépendances entre tous les projets
    generate_reports(auditors)  # Génère les rapports Markdown
    print_global_summary(auditors)  # Affiche le résumé final