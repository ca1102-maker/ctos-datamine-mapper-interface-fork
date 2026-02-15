/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './pages/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
    './app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: ['"Helvetica Neue"', 'Helvetica', 'Arial', 'ui-sans-serif', 'system-ui', '-apple-system', '"Segoe UI"', 'sans-serif'],
      },
      colors: {
        primary: {
          50: '#e0f7fa',
          100: '#b2ebf2',
          200: '#80deea',
          300: '#4dd0e1',
          400: '#26c6da',
          500: '#00bcd4',
          600: '#00acc1',
          700: '#0097a7',
          800: '#00838f',
          900: '#006064',
        },
        dark: {
          bg: '#1a1a2e',
          'bg-secondary': '#0f0f1e',
          'bg-card': 'rgba(255, 255, 255, 0.05)',
          sidebar: '#16213e',
          'sidebar-secondary': '#0f1929',
        },
      },
      backgroundImage: {
        'gradient-radial': 'radial-gradient(var(--tw-gradient-stops))',
        'gradient-conic': 'conic-gradient(from 180deg at 50% 50%, var(--tw-gradient-stops))',
        'dark-gradient': 'linear-gradient(135deg, #1a1a2e 0%, #0f0f1e 100%)',
        'sidebar-gradient': 'linear-gradient(180deg, #16213e 0%, #0f1929 100%)',
      },
    },
  },
  plugins: [require("tailwindcss-animate")],
  darkMode: 'class',
}

