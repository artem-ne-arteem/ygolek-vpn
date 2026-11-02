import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: "#080d17", // фон страницы
        panel: "#0e1524", // карточки
        panel2: "#131c2f", // вложенные блоки, строки таблиц
        line: "rgba(148, 163, 184, 0.14)", // рамки
        muted: "#8b97ad", // второстепенный текст
        accent: "#2f7bff", // основной синий
        accent2: "#5b9bff",
        danger: "#f05252",
      },
      fontFamily: {
        sans: ["var(--font-sans)", "system-ui", "sans-serif"],
      },
      boxShadow: {
        card: "0 1px 0 rgba(255,255,255,0.03) inset, 0 20px 40px -24px rgba(0,0,0,0.6)",
        glow: "0 8px 30px -8px rgba(47, 123, 255, 0.55)",
      },
    },
  },
  plugins: [],
};

export default config;
