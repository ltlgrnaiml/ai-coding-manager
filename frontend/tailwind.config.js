/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // xAI-inspired dark theme
        'xai-dark': '#0a0a0f',
        'xai-darker': '#050508',
        'xai-accent': '#00d4ff',
        'xai-accent-dim': '#0099bb',
      },
    },
  },
  plugins: [],
}
