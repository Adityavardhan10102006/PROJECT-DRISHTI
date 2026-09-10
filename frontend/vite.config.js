import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

const frontendPort = process.env.FRONTEND_PORT ? parseInt(process.env.FRONTEND_PORT, 10) : 3000;
const backendPort = process.env.BACKEND_PORT ? parseInt(process.env.BACKEND_PORT, 10) : 8000;
const backendHost = process.env.BACKEND_HOST || "localhost";
const backendUrl = `http://${backendHost}:${backendPort}`;

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    port: frontendPort,
    // Proxy API calls to FastAPI backend (avoids CORS during dev)
    proxy: {
      "/auth": {
        target: backendUrl,
        changeOrigin: true,
      },
      "/predict": {
        target: backendUrl,
        changeOrigin: true,
      },
      "/health": {
        target: backendUrl,
        changeOrigin: true,
      },
      "/ready": {
        target: backendUrl,
        changeOrigin: true,
      },
      "/alerts": {
        target: backendUrl,
        changeOrigin: true,
      },
      "/cases": {
        target: backendUrl,
        changeOrigin: true,
      },
      "/transactions": {
        target: backendUrl,
        changeOrigin: true,
      },
      "/analytics": {
        target: backendUrl,
        changeOrigin: true,
      },
      "/datasets": {
        target: backendUrl,
        changeOrigin: true,
      },
      "/audit-logs": {
        target: backendUrl,
        changeOrigin: true,
      },
      "/intelligence": {
        target: backendUrl,
        changeOrigin: true,
      },
      "/search": {
        target: backendUrl,
        changeOrigin: true,
      },
      "/atms": {
        target: backendUrl,
        changeOrigin: true,
      },
      "/integration": {
        target: backendUrl,
        changeOrigin: true,
      },
      "/api": {
        target: backendUrl,
        changeOrigin: true,
      },
    },
  },
});
