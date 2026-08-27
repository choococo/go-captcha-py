import { defineConfig } from 'vite'

export default defineConfig({
  server: { proxy: { '/captcha': 'http://127.0.0.1:9000' } }
})
