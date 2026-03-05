/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        brand: {
          50: '#f0f4ff',
          100: '#dce8ff',
          200: '#b3ccff',
          300: '#80a8ff',
          400: '#4d7eff',
          500: '#2563eb',
          600: '#1d4ed8',
          700: '#1e40af',
          800: '#1e3a8a',
          900: '#172759',
        },
        accent: {
          400: '#a78bfa',
          500: '#8b5cf6',
          600: '#7c3aed',
        },
        success: {
          400: '#34d399',
          500: '#10b981',
        },
        warn: {
          400: '#fbbf24',
          500: '#f59e0b',
        },
        danger: {
          400: '#f87171',
          500: '#ef4444',
        },
        surface: {
          900: '#0b0f1a',
          800: '#111827',
          700: '#1a2235',
          600: '#1f2d48',
          500: '#243352',
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'monospace'],
      },
      backgroundImage: {
        'hero-gradient': 'linear-gradient(135deg, #0b0f1a 0%, #111827 50%, #0e1628 100%)',
        'card-gradient': 'linear-gradient(145deg, rgba(26,34,53,0.9) 0%, rgba(17,24,39,0.95) 100%)',
        'brand-gradient': 'linear-gradient(135deg, #2563eb 0%, #7c3aed 100%)',
      },
      boxShadow: {
        'glow-brand': '0 0 20px rgba(37,99,235,0.4)',
        'glow-accent': '0 0 20px rgba(124,58,237,0.4)',
        'card': '0 4px 30px rgba(0,0,0,0.4)',
      },
      animation: {
        'fade-in': 'fadeIn 0.4s ease-out',
        'slide-up': 'slideUp 0.4s ease-out',
        'pulse-slow': 'pulse 3s cubic-bezier(0.4,0,0.6,1) infinite',
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        slideUp: {
          '0%': { opacity: '0', transform: 'translateY(16px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
      },
    },
  },
  plugins: [],
}
