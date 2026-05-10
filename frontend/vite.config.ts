import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'
import path from 'path'

// https://vite.dev/config/
const repositoryName = process.env.GITHUB_REPOSITORY?.split('/')[1]

export default defineConfig({
  base:
    process.env.GITHUB_ACTIONS && repositoryName
      ? `/${repositoryName}/`
      : '/',
  plugins: [react(), tailwindcss()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
})
