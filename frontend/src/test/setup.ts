/** Configuration commune des tests Vitest (matchers jest-dom : toBeInTheDocument, etc.). */
import '@testing-library/jest-dom/vitest'
import { cleanup } from '@testing-library/react'
import { afterEach } from 'vitest'

// Après chaque test : on démonte les composants et on vide la session,
// pour que les tests restent indépendants les uns des autres.
afterEach(() => {
  cleanup()
  sessionStorage.clear()
})
