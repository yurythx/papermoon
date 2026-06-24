import type { Config } from "tailwindcss";

const config: Config = {
  darkMode: ["class"],
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        surface: {
          "0": "rgb(var(--surface-0) / <alpha-value>)",
          "1": "rgb(var(--surface-1) / <alpha-value>)",
          "2": "rgb(var(--surface-2) / <alpha-value>)",
          "3": "rgb(var(--surface-3) / <alpha-value>)",
          "4": "rgb(var(--surface-4) / <alpha-value>)",
        },
        "text-primary": "rgb(var(--text-primary) / <alpha-value>)",
        "text-secondary": "rgb(var(--text-secondary) / <alpha-value>)",
        "text-tertiary": "rgb(var(--text-tertiary) / <alpha-value>)",
        "text-inverse": "rgb(var(--text-inverse) / <alpha-value>)",
        "border-subtle": "var(--border-subtle)",
        "border-default": "var(--border-default)",
        "border-focus": "var(--border-focus)",
        success: {
          DEFAULT: "rgb(var(--status-success-rgb) / <alpha-value>)",
          dark: "rgb(var(--status-success-dark-rgb) / <alpha-value>)",
          muted: "rgb(var(--status-success-rgb) / 0.12)",
        },
        warning: {
          DEFAULT: "rgb(var(--status-warning-rgb) / <alpha-value>)",
          dark: "rgb(var(--status-warning-dark-rgb) / <alpha-value>)",
          muted: "rgb(var(--status-warning-rgb) / 0.12)",
        },
        danger: {
          DEFAULT: "rgb(var(--status-danger-rgb) / <alpha-value>)",
          dark: "rgb(var(--status-danger-dark-rgb) / <alpha-value>)",
          muted: "rgb(var(--status-danger-rgb) / 0.12)",
        },
        info: {
          DEFAULT: "rgb(var(--status-info-rgb) / <alpha-value>)",
          dark: "rgb(var(--status-info-dark-rgb) / <alpha-value>)",
          muted: "rgb(var(--status-info-rgb) / 0.12)",
        },
        brand: {
          emerald: "rgb(var(--brand-emerald-rgb) / <alpha-value>)",
          accent: "rgb(var(--papermoon-accent-rgb) / <alpha-value>)",
          amber: "rgb(var(--status-warning-rgb) / <alpha-value>)",
          cyan: "rgb(var(--brand-cyan-rgb) / <alpha-value>)",
        },
        "service-whatsapp": "rgb(var(--service-whatsapp) / <alpha-value>)",
      },
      fontFamily: {
        sans: ["var(--font-geist)", "Inter", "DM Sans", "system-ui", "sans-serif"],
        mono: ["var(--font-geist-mono)", "JetBrains Mono", "Fira Code", "monospace"],
      },
      fontSize: {
        xs: ["11px", { lineHeight: "1.4", letterSpacing: "0.02em" }],
        sm: ["13px", { lineHeight: "1.5", letterSpacing: "0.01em" }],
        base: ["15px", { lineHeight: "1.6" }],
        lg: ["17px", { lineHeight: "1.5", fontWeight: "500" }],
        xl: ["20px", { lineHeight: "1.4", fontWeight: "600" }],
        "2xl": ["24px", { lineHeight: "1.3", fontWeight: "700" }],
        "3xl": ["30px", { lineHeight: "1.2", fontWeight: "700" }],
        display: ["42px", { lineHeight: "1.1", letterSpacing: "-0.03em", fontWeight: "800" }],
      },
      borderRadius: {
        micro: "4px",
        sm: "6px",
        DEFAULT: "8px",
        md: "10px",
        lg: "12px",
        xl: "16px",
        "2xl": "24px",
      },
      boxShadow: {
        sm: "var(--elevation-shadow-sm)",
        md: "var(--elevation-shadow-md)",
        lg: "var(--elevation-shadow-lg)",
        "glow-emerald": "var(--elevation-glow-emerald)",
        "glow-accent": "var(--elevation-glow-accent)",
        "glow-amber": "var(--elevation-glow-amber)",
        "glow-danger": "var(--elevation-glow-danger)",
      },
      keyframes: {
        shimmer: {
          "0%": { backgroundPosition: "200% 0" },
          "100%": { backgroundPosition: "-200% 0" },
        },
        "pulse-soft": {
          "0%, 100%": { opacity: "1" },
          "50%": { opacity: "0.6" },
        },
        "scale-in": {
          "0%": { transform: "scale(0)", opacity: "0" },
          "70%": { transform: "scale(1.1)" },
          "100%": { transform: "scale(1)", opacity: "1" },
        },
        "slide-up": {
          "0%": { transform: "translateY(16px)", opacity: "0" },
          "100%": { transform: "translateY(0)", opacity: "1" },
        },
        "slide-right": {
          "0%": { transform: "translateX(-100%)" },
          "100%": { transform: "translateX(0)" },
        },
        "fade-in": {
          "0%": { opacity: "0" },
          "100%": { opacity: "1" },
        },
        marquee: {
          "0%": { transform: "translateX(0)" },
          "100%": { transform: "translateX(-50%)" },
        },
      },
      animation: {
        shimmer: "shimmer 1.5s infinite linear",
        "pulse-soft": "pulse-soft 2s ease-in-out infinite",
        "scale-in": "scale-in 200ms cubic-bezier(0.34,1.56,0.64,1)",
        "slide-up": "slide-up 240ms cubic-bezier(0,0,0.2,1)",
        "slide-right": "slide-right 300ms cubic-bezier(0,0,0.2,1)",
        "fade-in": "fade-in 200ms ease-out",
        marquee: "marquee 28s linear infinite",
      },
      transitionTimingFunction: {
        spring: "cubic-bezier(0.34,1.56,0.64,1)",
        smooth: "cubic-bezier(0.4,0,0.2,1)",
      },
    },
  },
  plugins: [],
};

export default config;
