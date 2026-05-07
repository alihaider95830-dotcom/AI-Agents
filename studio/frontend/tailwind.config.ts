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
      colors: {
        brand: {
          gold: '#F5C05A',
          ink: '#0F172A',
          mist: '#E6EEF6',
          ocean: '#0EA5A4',
          sand: '#F8EDD8',
        },
      },
      boxShadow: {
        panel: "0 24px 80px rgba(15, 23, 42, 0.12)",
        glow: "0 0 40px -10px rgba(161, 161, 170, 0.2)",
      },
      backgroundImage: {
        'grid-pattern': "url(\"data:image/svg+xml,%3Csvg width='40' height='40' viewBox='0 0 40 40' xmlns='http://www.w3.org/2000/svg'%3E%3Cpath d='M0 0h40v40H0V0zm20 20h20v20H20V20zM0 20h20v20H0V20zM20 0h20v20H20V0z' fill='%23fafafa' fill-opacity='0.4' fill-rule='evenodd'/%3E%3C/svg%3E\")",
      },
    },
  },
  plugins: [typography],
};

export default config;
