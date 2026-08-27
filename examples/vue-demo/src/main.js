import Vue from 'vue'
import GoCaptcha from 'go-captcha-vue'
import 'go-captcha-vue/dist/style.css'
import App from './App.vue'

Vue.use(GoCaptcha)

new Vue({
  render: h => h(App)
}).$mount('#app')
