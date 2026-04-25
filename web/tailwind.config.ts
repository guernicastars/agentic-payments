import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: {
          900: "#0b0d12",
          800: "#11151c",
          700: "#202733",
          500: "#8792a0",
          300: "#b7c0ca",
          100: "#dce3ea",
          50: "#f5f7fa",
        },
        teal: { 500: "#2dd4bf" },
        risk: {
          critical: "#e5484d",
          high: "#f97316",
          medium: "#f2c94c",
          low: "#2dd4bf",
        },
      },
      fontFamily: {
        mono: ["ui-monospace", "SFMono-Regular", "Menlo", "monospace"],
      },
      animation: {
        flash: "flash 1s ease-out 1",
        pulseDot: "pulseDot 1.6s ease-in-out infinite",
      },
      keyframes: {
        flash: {
          "0%": { backgroundColor: "rgba(229,72,77,0.4)" },
          "100%": { backgroundColor: "transparent" },
        },
        pulseDot: {
          "0%,100%": { opacity: "0.45" },
          "50%": { opacity: "1" },
        },
      },
    },
  },
  plugins: [],
};
export default config;
