import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";

/**
 * Vite config — https://vitejs.dev/config/
 *
 * Структура проекта:
 * - В режиме разработки (vite dev) порт 5173, proxy к API на :8000
 * - В продакшене (vite build) собирается статика в dist/
 */
export default defineConfig(({ mode }) => {
  const isDev = mode !== "production";

  return {
    base: "/",
    build: {
      sourcemap: isDev,
      minify: !isDev,
    },
    plugins: [react(), tailwindcss()],
    resolve: {
      alias: {
        "@": "/src",
      },
    },
    server: {
      host: "0.0.0.0",
      port: 5173,
      strictPort: true,
      proxy: {
        "/api": {
          target: "http://localhost:8080",
          changeOrigin: true,
        },
      },
    },
    preview: {
      host: "0.0.0.0",
      port: 4173,
    },
  };
});
