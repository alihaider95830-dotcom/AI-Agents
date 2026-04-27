import type { Config } from "tailwindcss";
import typography from "@tailwindcss/typography";

const config: Config = {
  darkMode: "class",
  content: [
    "./src/app/**/*.{ts,tsx}",
    "./src/components/**/*.{ts,tsx}",
  ],
  theme: {
    extend: {
      boxShadow: {
        panel: "0 24px 80px rgba(15, 23, 42, 0.12)",
      },
      colors: {
        brand: {
          ink: "#102542",
          ocean: "#2b5f75",
          mist: "#d7e8ee",
          sand: "#f5efe7",
          gold: "#d4a373",
        },
      },
    },
  },
  plugins: [typography],
};

export default config;
