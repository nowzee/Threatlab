import { fileURLToPath, URL } from 'node:url'

import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// https://vite.dev/config/
export default defineConfig({
  plugins: [
    vue(),
  ],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url))
    },
  },
  build: {
    rollupOptions: {
      output: {
        // Sépare les grosses dépendances dans leurs propres chunks : le bundle
        // principal repasse sous 500 kB et les libs sont mises en cache à part.
        manualChunks(id) {
          if (id.includes('node_modules')) {
            if (id.includes('chart.js') || id.includes('vue-chartjs')) return 'charts'
            if (id.includes('vue-i18n')) return 'i18n'
            return 'vendor'
          }
        },
      },
    },
  },
})
