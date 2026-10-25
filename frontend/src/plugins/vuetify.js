import "vuetify/styles";
import "@mdi/font/css/materialdesignicons.css";
import { createVuetify } from "vuetify";
import { aliases, mdi } from "vuetify/iconsets/mdi";

const savedTheme = localStorage.getItem("api_sentinel_theme") || "dark";

export default createVuetify({
  icons: {
    defaultSet: "mdi",
    aliases,
    sets: {
      mdi,
    },
  },
  theme: {
    defaultTheme: savedTheme,
    themes: {
      dark: {
        dark: true,
        colors: {
          background: "#121214",       // Charcoal workspace background
          surface: "#18181b",          // Dark zinc surface
          "surface-variant": "#27272a", // Zinc-800 secondary surfaces
          primary: "#7c3aed",          // Restrained violet
          "primary-darken-1": "#6d28d9",
          secondary: "#10b981",        // Emerald
          accent: "#8b5cf6",           // Light violet
          info: "#06b6d4",             // Cyan
          success: "#10b981",          // Emerald green
          warning: "#f59e0b",          // Amber
          error: "#ef4444",            // Rose red
          outline: "#2e2e33",          // Subtle border
        },
      },
      light: {
        dark: false,
        colors: {
          background: "#f8fafc",        // Slate 50 clean workspace
          surface: "#ffffff",           // Pure white
          "surface-variant": "#f1f5f9", // Slate 100 secondary surfaces
          primary: "#7c3aed",           // Violet
          "primary-darken-1": "#6d28d9",
          secondary: "#059669",         // Emerald green
          accent: "#8b5cf6",            // Light violet
          info: "#0284c7",              // Sky blue
          success: "#10b981",           // Emerald green
          warning: "#d97706",           // Amber
          error: "#dc2626",             // Red
          outline: "#e2e8f0",           // Subtle border
        },
      },
    },
  },
});
