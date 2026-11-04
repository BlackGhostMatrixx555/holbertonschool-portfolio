// Importe les règles JavaScript recommandées par ESLint (erreurs probables, bonnes pratiques de base).
import js from '@eslint/js'

// Importe les définitions de variables globales par environnement (ici, celles du navigateur : window, document...).
import globals from 'globals'

// Plugin qui vérifie le respect des règles des hooks React (useState, useEffect...), notamment leur ordre et leur appel au niveau racine.
import reactHooks from 'eslint-plugin-react-hooks'

// Plugin qui vérifie la compatibilité avec le Fast Refresh de Vite : un fichier doit exporter uniquement des composants pour que le rechargement à chaud fonctionne.
import reactRefresh from 'eslint-plugin-react-refresh'

// Ensemble de règles et parseur TypeScript pour ESLint (typage, syntaxe TS).
import tseslint from 'typescript-eslint'

// defineConfig : fonction d'aide qui valide et type la configuration (format "flat config", ESLint 9+).
// globalIgnores : permet d'ignorer des dossiers pour toute la configuration.
import { defineConfig, globalIgnores } from 'eslint/config'

// Export par défaut de la configuration, lue automatiquement par ESLint.
export default defineConfig([
  // Ignore globalement le dossier 'dist' (fichiers générés par le build, inutiles à analyser).
  globalIgnores(['dist']),

  // Bloc de configuration appliqué uniquement aux fichiers TypeScript et TSX.
  {
    // Motif glob : tous les fichiers .ts et .tsx, dans tous les sous-dossiers.
    files: ['**/*.{ts,tsx}'],

    // "extends" regroupe plusieurs ensembles de règles à appliquer dans ce bloc.
    extends: [
      // Règles JavaScript recommandées par ESLint.
      js.configs.recommended,

      // Règles TypeScript recommandées (ex. interdiction de certains usages de "any").
      tseslint.configs.recommended,

      // Règles des hooks React en mode "flat" (format moderne), niveau recommandé.
      reactHooks.configs.flat.recommended,

      // Règles de compatibilité Fast Refresh, préréglées pour Vite.
      reactRefresh.configs.vite,
    ],

    // Options de langage : définit l'environnement d'exécution attendu.
    languageOptions: {
      // Déclare les globales du navigateur pour éviter les faux positifs "variable non définie" (ex. window, document).
      globals: globals.browser,
    },
  },
])