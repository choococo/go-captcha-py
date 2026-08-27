<template>
  <div id="captcha-app">
    <h1>go-captcha-py × Vue Demo</h1>
    <p class="tip">后端为 examples/fastapi_server.py（uv run --extra fastapi uvicorn ...）</p>

    <div class="grid">
      <!-- ======================= Click (text) ======================= -->
      <section class="card">
        <h2>① 点击验证码（文字）</h2>
        <div v-if="clickState.captchaId">
          <GoClick
            ref="click"
            :data="clickData"
            :config="clickConfig"
            :events="clickEvents"
          />
        </div>
        <p class="result" :class="clickState.verified ? 'ok' : 'fail'">{{ clickState.message }}</p>
      </section>

      <!-- ======================= Slide (basic) ======================= -->
      <section class="card">
        <h2>② 滑动拼图验证码</h2>
        <div v-if="slideState.captchaId">
          <GoSlide
            ref="slide"
            :data="slideData"
            :events="slideEvents"
          />
        </div>
        <p class="result" :class="slideState.verified ? 'ok' : 'fail'">{{ slideState.message }}</p>
      </section>

      <!-- ======================= Drag-Drop (SlideRegion) ======================= -->
      <section class="card">
        <h2>③ 拖拽拼图验证码</h2>
        <div v-if="dragState.captchaId">
          <GoSlideRegion
            ref="drag"
            :data="dragData"
            :events="dragEvents"
          />
        </div>
        <p class="result" :class="dragState.verified ? 'ok' : 'fail'">{{ dragState.message }}</p>
      </section>

      <!-- ======================= Rotate ======================= -->
      <section class="card">
        <h2>④ 旋转验证码</h2>
        <div v-if="rotateState.captchaId">
          <GoRotate
            ref="rotate"
            :data="rotateData"
            :config="rotateConfig"
            :events="rotateEvents"
          />
        </div>
        <p class="result" :class="rotateState.verified ? 'ok' : 'fail'">{{ rotateState.message }}</p>
      </section>
    </div>
  </div>
</template>

<script>
// 组件名来自 go-captcha-vue@^1 导出: Click / Slide / SlideRegion / Rotate
import { Click as GoClick, Slide as GoSlide, SlideRegion as GoSlideRegion, Rotate as GoRotate } from 'go-captcha-vue'

const b64Url = raw => (raw.startsWith('data:') ? raw : `data:image/jpeg;base64,${raw}`)
const b64UrlPng = raw => (raw.startsWith('data:') ? raw : `data:image/png;base64,${raw}`)

async function postForm(url, data) {
  const body = new URLSearchParams(data)
  const res = await fetch(url, { method: 'POST', body })
  if (res.status === 403) return { code: 1, captcha_verified: false, message: 'captcha 已过期，请刷新重试' }
  return res.json()
}

export default {
  name: 'App',
  components: { GoClick, GoSlide, GoSlideRegion, GoRotate },
  data() {
    return {
      e2e: false,
      // ---- click ----
      clickData: { image: '', thumb: '' },
      clickConfig: { width: 300, height: 220, thumbWidth: 150, thumbHeight: 40, title: '请在下图依次点击', buttonText: '确认' },
      clickState: { captchaId: '', message: '等待生成…', verified: false, answer: null },
      // ---- slide ----
      slideData: { image: '', thumb: '', thumbX: 0, thumbY: 0, thumbWidth: 0, thumbHeight: 0 },
      slideState: { captchaId: '', message: '等待生成…', verified: false, answer: null },
      // ---- drag ----
      dragData: { image: '', thumb: '', thumbX: 0, thumbY: 0, thumbWidth: 0, thumbHeight: 0 },
      dragState: { captchaId: '', message: '等待生成…', verified: false, answer: null },
      // ---- rotate ----
      rotateData: { image: '', thumb: '', thumbSize: 0 },
      rotateConfig: { size: 220 },
      rotateState: { captchaId: '', message: '等待生成…', verified: false, answer: null }
    }
  },
  computed: {
    clickEvents() {
      return {
        click: () => {},
        confirm: async (dots, reset) => {
          const d = this.clickState
          const dotStr = dots.map(p => `${p.x},${p.y}`).join(';')
          const r = await postForm('/captcha/click/verify', { dots: dotStr, captcha_id: d.captchaId })
          d.verified = !!r.captcha_verified
          d.message = r.captcha_verified ? '✅ 验证通过' : `❌ ${r.message || '验证失败'}`
          if (!r.captcha_verified) { reset(); this.loadClick() }
        },
        refresh: () => this.loadClick(),
        close: () => {}
      }
    },
    slideEvents() {
      return {
        confirm: async ({ x, y }, reset) => {
          const d = this.slideState
          const r = await postForm('/captcha/slide/verify', { point: `${x},${y}`, captcha_id: d.captchaId })
          d.verified = !!r.captcha_verified
          d.message = r.captcha_verified ? '✅ 验证通过' : `❌ ${r.message || '验证失败'}`
          if (!r.captcha_verified) { reset(); this.loadSlide() }
        },
        refresh: () => this.loadSlide(),
        close: () => {}
      }
    },
    dragEvents() {
      return {
        confirm: async ({ x, y }, reset) => {
          const d = this.dragState
          const r = await postForm('/captcha/slide/verify', { point: `${x},${y}`, captcha_id: d.captchaId })
          d.verified = !!r.captcha_verified
          d.message = r.captcha_verified ? '✅ 验证通过' : `❌ ${r.message || '验证失败'}`
          if (!r.captcha_verified) { reset(); this.loadDrag() }
        },
        refresh: () => this.loadDrag(),
        close: () => {}
      }
    },
    rotateEvents() {
      return {
        confirm: async (angle, reset) => {
          const d = this.rotateState
          const r = await postForm('/captcha/rotate/verify', { angle: String(angle), captcha_id: d.captchaId })
          d.verified = !!r.captcha_verified
          d.message = r.captcha_verified ? '✅ 验证通过' : `❌ ${r.message || '验证失败'}`
          if (!r.captcha_verified) { reset(); this.loadRotate() }
        },
        refresh: () => this.loadRotate(),
        close: () => {}
      }
    }
  },
  mounted() {
    this.e2e = new URLSearchParams(location.search).has('e2e')
    this.loadClick()
    this.loadSlide()
    this.loadDrag()
    this.loadRotate()
  },
  methods: {
    async loadClick() {
      const d = this.clickState
      d.message = '加载中…'; d.verified = false
      const res = await fetch('/captcha/click' + (this.e2e ? '?debug_answer=1' : ''))
      const r = await res.json()
      d.captchaId = r.captcha_id
      d.answer = r.answer || null  // only present with GOCAPTCHA_DEBUG=1
      this.clickData.image = b64Url(r.image_base64)
      this.clickData.thumb = b64UrlPng(r.thumb_base64)
      d.message = '请依次点击缩略图中出现的文字'
    },
    async loadSlide() {
      const d = this.slideState
      d.message = '加载中…'; d.verified = false
      const res = await fetch('/captcha/slide' + (this.e2e ? '?debug_answer=1' : ''))
      const r = await res.json()
      d.captchaId = r.captcha_id
      d.answer = r.answer || null
      const img = new Image()
      img.onload = () => {
        this.slideData.image = b64Url(r.image_base64)
        this.slideData.thumb = b64UrlPng(r.tile_base64)
        this.slideData.thumbX = r.tile_x
        this.slideData.thumbY = r.tile_y
        this.slideData.thumbWidth = img.width
        this.slideData.thumbHeight = img.height
        d.message = '拖动滑块完成拼图'
      }
      img.src = b64UrlPng(r.tile_base64)
    },
    async loadDrag() {
      const d = this.dragState
      d.message = '加载中…'; d.verified = false
      const res = await fetch('/captcha/slide?drag=true' + (this.e2e ? '&debug_answer=1' : ''))
      const r = await res.json()
      d.captchaId = r.captcha_id
      d.answer = r.answer || null
      const img = new Image()
      img.onload = () => {
        this.dragData.image = b64Url(r.image_base64)
        this.dragData.thumb = b64UrlPng(r.tile_base64)
        this.dragData.thumbX = r.tile_x
        this.dragData.thumbY = r.tile_y
        this.dragData.thumbWidth = img.width
        this.dragData.thumbHeight = img.height
        d.message = '拖拽拼图到缺口处'
      }
      img.src = b64UrlPng(r.tile_base64)
    },
    async loadRotate() {
      const d = this.rotateState
      d.message = '加载中…'; d.verified = false
      const res = await fetch('/captcha/rotate')
      const r = await res.json()
      d.captchaId = r.captcha_id
      d.answer = r.answer || null
      this.rotateData.image = b64UrlPng(r.image_base64)
      this.rotateData.thumb = b64UrlPng(r.thumb_base64)
      this.rotateData.thumbSize = r.thumb_size || 150
      this.rotateConfig.size = r.size || 220
      d.message = '旋转图片至正确角度'
    }
  }
}
</script>

<style>
body { margin: 0; background: #f4f6fa; font-family: -apple-system, 'PingFang SC', sans-serif; }
/* go-captcha-vue@1.0.7 bug: .gc-loading spinner has no hide condition and
   stays overlaid on the image center (z-index:1) after loading, covering
   the middle characters. Hide it once the picture is rendered. */
.gc-picture ~ .gc-loading,
.gc-body:has(.gc-picture) .gc-loading { display: none !important; }
.go-captcha .gc-loading:has(svg) { display: none !important; }
#captcha-app { max-width: 1060px; margin: 0 auto; padding: 24px 16px 60px; }
h1 { font-size: 22px; }
.tip { color: #888; font-size: 13px; margin: 4px 0 20px; }
.grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(340px, 1fr)); gap: 16px; }
.card { background: #fff; border-radius: 12px; padding: 16px; box-shadow: 0 2px 8px rgba(0,0,0,.06); }
.card h2 { font-size: 15px; margin: 0 0 12px; }
.result { font-size: 13px; margin: 10px 0 0; }
.result.ok { color: #16a34a; }
.result.fail { color: #dc2626; }
</style>
