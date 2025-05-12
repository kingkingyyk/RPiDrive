import { defineConfig } from "vite";
import react from "@vitejs/plugin-react-swc";

// https://vitejs.dev/config/
export default defineConfig({
  base: "/drive",
  plugins: [react()],
  build: {
    outDir: "build",
    emptyOutDir: true,
    assetsDir: "static",
  },
  server: {
    port: 4200,
    proxy: {
      "/drive/ui-api": "http://localhost:8000",
      "/drive/download": "http://localhost:8000",
    },
  },
});
