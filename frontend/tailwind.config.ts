import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      backgroundImage: {
        "gradient-radial": "radial-gradient(var(--tw-gradient-stops))",
        "gradient-conic":
          "conic-gradient(from 180deg at 50% 50%, var(--tw-gradient-stops))",
      },
      colors: {
        'hypurple': '#4E11B7',
        'hygreen': '#4B7F52',
        'hyred': '#C42348',
        'hyblue': '#A6E1FA',
        'hyyellow': '#FCBA04',
        'hygrey': '#8A8A8A',
      },
    },
  },
  plugins: [],
};
export default config;
