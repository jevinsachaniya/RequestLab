import "vuetify/styles";
import "@mdi/font/css/materialdesignicons.css";
import { createVuetify } from "vuetify";
import { aliases, mdi } from "vuetify/iconsets/mdi";

export default createVuetify({
  icons: {
    defaultSet: "mdi",
    aliases,
    sets: {
      mdi,
    },
  },
  theme: {
    defaultTheme: "dark",
    themes: {
      dark: {
        dark: true,
        colors: {
          background: "#181818",
          surface: "#1e1e1e",
          "surface-variant": "#282828",
          primary: "#0b5fff",
          "primary-darken-1": "#0056e0",
          secondary: "#9aa0a6",
          accent: "#79c0ff",
          info: "#38bdf8",
          success: "#10b981",
          warning: "#f59e0b",
          error: "#ef4444",
          outline: "#333333",
        },
      },
    },
  },
});
