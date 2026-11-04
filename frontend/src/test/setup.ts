// Ajoute des matchers spécifiques au DOM à Vitest, comme toBeInTheDocument(), toHaveTextContent() ou toBeDisabled().
// Le suffixe "/vitest" les branche sur l'API expect de Vitest. L'import seul suffit : il étend expect par effet de bord.
import '@testing-library/jest-dom/vitest'

// cleanup : démonte tous les composants rendus pendant le test précédent (retire le DOM créé par render()).
import { cleanup } from '@testing-library/react'

// afterEach : hook de Vitest qui exécute la fonction fournie après chaque test.
import { afterEach } from 'vitest'

// Exécuté après chaque test, pour que chaque test parte d'un état propre.
afterEach(() => {
  // Démonte les composants rendus. Testing Library le fait déjà automatiquement si globals est activé dans Vitest ; l'appel explicite rend le comportement visible et ne fait pas de mal.
  cleanup()

  // Vide le sessionStorage du navigateur simulé. C'est là que l'application garde probablement le token JWT ; sans ce nettoyage, un test connecté pourrait laisser un utilisateur connecté au test suivant.
  sessionStorage.clear()
})