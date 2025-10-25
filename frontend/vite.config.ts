import { defineConfig } from 'vite';
import vue from '@vitejs/plugin-vue';

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [vue()],
  server: {
    host: '0.0.0.0',
    port: 5173,
    proxy: {
      '/sim': {
        target: process.env.VITE_BACKEND_URL ?? 'http://localhost:8000',
        changeOrigin: true,
      },
      '/ws': {
        target: process.env.VITE_BACKEND_URL ?? 'http://localhost:8000',
        ws: true,
      },
    },
  },
});
