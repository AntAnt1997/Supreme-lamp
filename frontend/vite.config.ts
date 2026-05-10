import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'
import path from 'path'

// https://vite.dev/config/
const repositoryPath = process.env.GITHUB_REPOSITORY?.trim()
const repoName = repositoryPath?.includes('/')
  ? repositoryPath.split('/').filter(Boolean).at(-1)
  : undefined

export default defineConfig({
  base:
    process.env.GITHUB_ACTIONS && repoName
      ? `/${repoName}/`
      : '/',
  plugins: [react(), tailwindcss()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
})
