import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue2'

export default defineConfig({
  plugins: [vue()],
  server: {
    port: 5173,
    proxy: {
      // 用 127.0.0.1 避免localhost解析到IPv6被其他代理(如gvproxy)抢占
      '/captcha': 'http://127.0.0.1:9000'
    }
  }
})
