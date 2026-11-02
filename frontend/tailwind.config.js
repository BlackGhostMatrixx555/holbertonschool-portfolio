/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        navy: { DEFAULT: '#1B2454', light: '#2F3C7E', dark: '#0F1533' },
        coral: { DEFAULT: '#F9646A', dark: '#E14A50' },
        gold: '#F3C24B',
        cream: '#FAFAFD',
        surface: '#F3F4FA',
        ink: '#1D2140',
        muted: '#6A6E8C',
      },
      fontFamily: {
        sans: ['Inter', 'sans-serif'],
        display: ['Fraunces', 'serif'],
      },
    },
  },
  plugins: [],
}
