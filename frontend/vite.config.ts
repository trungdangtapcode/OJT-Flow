import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";

export default defineConfig({
  plugins: [react(), tailwindcss()],
  build: {
    rollupOptions: {
      output: {
        manualChunks(id) {
          if (!id.includes("node_modules")) return undefined;
          if (id.includes("@tanstack")) return "tanstack";
          if (id.includes("@radix-ui")) return "radix";
          if (id.includes("react") || id.includes("scheduler")) return "react";
          return "vendor";
        },
      },
    },
  },
  server: {
    port: 15173,
    strictPort: true,
    proxy: {
      "/api": {
        target: process.env.VITE_API_PROXY_TARGET ?? "http://localhost:18000",
        changeOrigin: true,
        headers: {
          Connection: "keep-alive",
        },
      },
      "/health": {
        target: process.env.VITE_API_PROXY_TARGET ?? "http://localhost:18000",
        changeOrigin: true,
      },
    },
  },
  preview: {
    port: 15173,
    strictPort: true,
  },
});
