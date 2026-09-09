import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    // Proxy API calls to FastAPI backend (avoids CORS during dev)
    proxy: {
      "/predict": {
        target:       "http://localhost:8000",
        changeOrigin: true,
      },
      "/health": {
        target:       "http://localhost:8000",
        changeOrigin: true,
      },
      "/ready": {
        target:       "http://localhost:8000",
        changeOrigin: true,
      },
      "/alerts": {
        target:       "http://localhost:8000",
        changeOrigin: true,
      },
      "/api": {
        target:       "http://localhost:8000",
        changeOrigin: true,
      },
    },
  },
});
