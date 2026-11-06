/** @type {import('tailwindcss').Config} */
export default {
  darkMode: "class",
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        ink: {
          950: "#07070B",
          900: "#0B0B10",
          850: "#0F0F16",
          800: "#13131C",
          700: "#1B1B26",
          600: "#262633",
        },
        ember: {
          50: "#FDF4F2",
          100: "#FAE7E3",
          200: "#F3CAC2",
          300: "#FDB773",
          400: "#EB895B",
          500: "#DA6556",
          600: "#A14646",
          700: "#873A3A",
          800: "#6B2F2F",
          900: "#4B2222",
          950: "#2A1414",
        },
      },
      fontFamily: {
        sans: ["Inter", "ui-sans-serif", "system-ui", "sans-serif"],
        mono: ["JetBrains Mono", "ui-monospace", "SFMono-Regular", "monospace"],
      },
      boxShadow: {
        glow: "0 0 60px -18px rgba(218, 101, 86, 0.55)",
        "glow-soft": "0 0 40px -20px rgba(235, 137, 91, 0.45)",
        card: "0 24px 70px -30px rgba(0, 0, 0, 0.9)",
        "card-light": "0 24px 60px -34px rgba(30, 20, 15, 0.22)",
      },
      backgroundImage: {
        "ember-gradient":
          "linear-gradient(120deg, #A14646 0%, #DA6556 48%, #EB895B 100%)",
        "ember-text":
          "linear-gradient(110deg, #FDB773 0%, #EB895B 42%, #DA6556 100%)",
      },
      keyframes: {
        "fade-up": {
          "0%": { opacity: "0", transform: "translateY(10px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
        "fade-in": {
          "0%": { opacity: "0", transform: "scale(0.99)" },
          "100%": { opacity: "1", transform: "scale(1)" },
        },
        "pulse-glow": {
          "0%, 100%": { opacity: "0.55" },
          "50%": { opacity: "1" },
        },
        float: {
          "0%, 100%": { transform: "translateY(0)" },
          "50%": { transform: "translateY(-8px)" },
        },
        shimmer: {
          "0%": { backgroundPosition: "200% 0" },
          "100%": { backgroundPosition: "-200% 0" },
        },
        "scan-line": {
          "0%": { transform: "translateX(-100%)" },
          "100%": { transform: "translateX(200%)" },
        },
      },
      animation: {
        "fade-up": "fade-up 0.5s ease-out both",
        "fade-in": "fade-in 0.6s ease-out both",
        "pulse-glow": "pulse-glow 3s ease-in-out infinite",
        float: "float 6s ease-in-out infinite",
        shimmer: "shimmer 2.4s linear infinite",
        "scan-line": "scan-line 1.6s ease-in-out infinite",
      },
    },
  },
  plugins: [],
};
