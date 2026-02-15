/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      fontFamily: {
        sans: ['Inter', 'system-ui', '-apple-system', 'sans-serif'],
      },
      colors: {
        mtg: {
          white: '#F8F6F0',
          blue: '#0E68AB',
          black: '#150B00',
          red: '#D3202A',
          green: '#00733E',
          gold: '#C9A74C',
        },
        terracota: {
          50:  '#F5EFE0',
          100: '#EFE6D6',
          200: '#E8DECA',
          300: '#D3C5AE',
          400: '#8A7A6A',
          500: '#C65F3C',
          600: '#B34924',
          700: '#5A4634',
          800: '#3E2E22',
          900: '#382A20',
          950: '#2A2018',
          1000: '#231B14',
        },
      },
    },
  },
  plugins: [],
}
