/** @type {import('tailwindcss').Config} */
export default {
  darkMode: 'class',
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      fontFamily: {
        sans: ['"IBM Plex Sans"', 'sans-serif'],
        display: ['"Space Grotesk"', 'sans-serif'],
      },
      colors: {
        ibm: {
          blue: '#0F62FE',
          blueDeep: '#0043CE',
          ink: '#0F172A',
          surface: '#FFFFFF',
          soft: '#F8FAFC',
          line: '#E2E8F0',
          text: '#334155',
        },
      },
      boxShadow: {
        panel: '0 16px 32px -20px rgba(15, 23, 42, 0.22)',
        glow: '0 14px 28px -18px rgba(15, 98, 254, 0.34)',
        glass: '0 20px 60px -34px rgba(15, 23, 42, 0.45)',
        float: '0 28px 90px -44px rgba(15, 23, 42, 0.58)',
      },
      keyframes: {
        fadeUp: {
          '0%': { opacity: '0', transform: 'translateY(14px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        shimmerSoft: {
          '0%': { opacity: '0.45' },
          '50%': { opacity: '1' },
          '100%': { opacity: '0.45' },
        },
        pulseGlow: {
          '0%, 100%': { opacity: '0.45', transform: 'scale(1)' },
          '50%': { opacity: '0.9', transform: 'scale(1.04)' },
        },
      },
      animation: {
        fadeUp: 'fadeUp 0.55s ease-out both',
        shimmerSoft: 'shimmerSoft 1.8s ease-in-out infinite',
        pulseGlow: 'pulseGlow 2.4s ease-in-out infinite',
      },
    },
  },
  plugins: [],
};
