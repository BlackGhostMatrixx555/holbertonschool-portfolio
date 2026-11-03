# CampOrga – Front-end

Interface web de CampOrga : React 19, TypeScript, Vite, Tailwind CSS,
React Router, TanStack Query, React Hook Form + Zod.

## Démarrer

```bash
cp .env.example .env      # URL de l'API (par défaut http://localhost:8000)
npm install
npm run dev               # http://localhost:5173
```

L'API doit tourner en parallèle (`docker compose up -d` à la racine du projet).

## Scripts

| Commande | Rôle |
| --- | --- |
| `npm run dev` | Serveur de développement avec rechargement à chaud |
| `npm run build` | Vérification TypeScript puis build de production dans `dist/` |
| `npm test` | Tests unitaires et de composants (Vitest + Testing Library) |
| `npm run lint` | Analyse statique (ESLint) |

## Organisation

```
src/
├── api/          client HTTP, une fonction par route, types de l'API
├── auth/         contexte d'authentification et garde de routes
├── components/   composants réutilisables (formulaires, chatbot, onglets…)
├── lib/          dates, saisons, schéma de validation des camps
├── pages/        une page par écran (public, organisateur, admin)
└── test/         configuration et outils de test
```

## Pages

| URL | Accès | Rôle |
| --- | --- | --- |
| `/` | Public | Liste des camps publiés |
| `/camps/:slug` | Public | Landing page : compte à rebours saisonnier, inscription, contact, chatbot, partage LinkedIn |
| `/connexion` | Public | Connexion des organisateurs |
| `/espace` | Organisateur | Tableau de bord |
| `/espace/camps/nouveau` · `/espace/camps/:id/modifier` | Organisateur | Formulaire de camp |
| `/espace/camps/:id` | Organisateur | Inscriptions, landing page, messages, statistiques du chatbot |
| `/espace/utilisateurs` · `/espace/sauvegardes` | Super admin | Comptes et exports |

## Accessibilité

- Labels reliés aux champs, erreurs annoncées (`aria-invalid`, `aria-describedby`, `role="alert"`)
- Navigation clavier complète, focus visible, lien d'évitement, onglets WAI-ARIA (flèches gauche/droite)
- Contrastes WCAG AA, respect de `prefers-reduced-motion`
- Audit axe-core : aucune violation WCAG 2.1 AA sur les pages principales
