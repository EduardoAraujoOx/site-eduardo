import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  base: '/ensino/veu-ignorancia/',
  build: {
    outDir: '../../ensino/veu-ignorancia',
    emptyOutDir: true,
  },
})
