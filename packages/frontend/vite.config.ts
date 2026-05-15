import { defineConfig } from "vite";
import eslintPlugin from "vite-plugin-eslint";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";

const devProxyTarget = process.env.VITE_DEV_PROXY_TARGET ?? "http://127.0.0.1:3801";

// https://vite.dev/config/
export default defineConfig({
  plugins: [
    tailwindcss(),
    react(),
    eslintPlugin({
      include: ["src/**/*.js", "src/**/*.jsx", "src/**/*.ts", "src/**/*.tsx"],
    }),
  ],
  server: {
    port: 3800,
    proxy: {
      "/api": {
        target: devProxyTarget,
        changeOrigin: true,
      },
    },
  },
});
