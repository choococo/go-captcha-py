import { defineConfig } from 'vite'
import solid from 'vite-plugin-solid'

export default defineConfig({
  plugins: [solid()],
  server: { proxy: { '/captcha': 'http://127.0.0.1:9000' } }
})
