import type { Config } from "tailwindcss";

const config: Config = {
  darkMode: "class",
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./lib/**/*.{js,ts,jsx,tsx,mdx}",
    "./config/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        brand: {
          blue: "#1D4ED8",
          "blue-hover": "#1E40AF",
          "blue-light": "#3B82F6",
          "blue-subtle": "rgba(29, 78, 216, 0.08)",
          navy: "#0F172A",
          "navy-deep": "#080C15",
          "navy-surface": "#131C31",
          slate: "#64748B",
          "slate-light": "#94A3B8",
          "gray-soft": "#E2E8F0",
          "gray-border": "rgba(226, 232, 240, 0.8)",
          "off-white": "#F8FAFC",
          white: "#FFFFFF",
        },
      },
      fontFamily: {
        sans: ["var(--font-sans)", "system-ui", "-apple-system", "sans-serif"],
        arabic: ["var(--font-arabic)", "'IBM Plex Sans Arabic'", "'Tajawal'", "sans-serif"],
      },
      boxShadow: {
        "architectural": "0 20px 40px -15px rgba(15, 23, 42, 0.07)",
        "architectural-dark": "0 20px 40px -15px rgba(0, 0, 0, 0.5)",
        "subtle": "0 2px 10px rgba(15, 23, 42, 0.04)",
      },
    },
  },
  plugins: [],
};

export default config;
