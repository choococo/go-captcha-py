import { render } from 'solid-js/web'
import GoCaptcha from 'go-captcha-solid'

const b64 = (raw, png) => (raw.startsWith('data:') ? raw : `data:image/${png ? 'png' : 'jpeg'};base64,${raw}`)

async function postForm(url, data) {
  const res = await fetch(url, { method: 'POST', body: new URLSearchParams(data) })
  if (res.status === 403) return { code: 1, captcha_verified: false, message: '已过期' }
  return res.json()
}

function App() {
  // 简化实现：直接用原生 signal 状态
  const state = { click: { id: '', image: '', thumb: '', msg: '加载中…', ok: false }, slide: { id: '', image: '', thumb: '', tx: 0, ty: 0, tw: 0, th: 0, msg: '加载中…', ok: false }, rotate: { id: '', image: '', thumb: '', size: 220, thumbSize: 150, msg: '加载中…', ok: false } }
  const els = {}

  const loadClick = async () => {
    const r = await (await fetch('/captcha/click')).json()
    state.click = { ...state.click, id: r.captcha_id, image: b64(r.image_base64), thumb: b64(r.thumb_base64, true), msg: '请依次点击文字', ok: false }
    renderCards()
  }
  const loadSlide = () => {
    fetch('/captcha/slide').then(r => r.json()).then(r => {
      const img = new Image()
      img.onload = () => { state.slide = { ...state.slide, id: r.captcha_id, image: b64(r.image_base64), thumb: b64(r.tile_base64, true), tx: r.tile_x, ty: r.tile_y, tw: img.width, th: img.height, msg: '拖动滑块完成拼图', ok: false }; renderCards() }
      img.src = b64(r.tile_base64, true)
    })
  }
  const loadRotate = async () => {
    const r = await (await fetch('/captcha/rotate')).json()
    state.rotate = { ...state.rotate, id: r.captcha_id, image: b64(r.image_base64, true), thumb: b64(r.thumb_base64, true), size: r.size || 220, thumbSize: r.thumb_size || 150, msg: '旋转图片至正确角度', ok: false }
    renderCards()
  }

  const clickEvents = {
    click: () => {},
    confirm: async (dots, reset) => {
      const r = await postForm('/captcha/click/verify', { dots: dots.map(p => `${p.x},${p.y}`).join(';'), captcha_id: state.click.id })
      state.click = { ...state.click, ok: !!r.captcha_verified, msg: r.captcha_verified ? '✅ 验证通过' : `❌ ${r.message || '验证失败'}` }
      renderCards()
      if (!r.captcha_verified) { reset(); loadClick() }
    },
    refresh: loadClick,
    close: () => {}
  }
  const slideEvents = {
    confirm: async ({ x, y }, reset) => {
      const r = await postForm('/captcha/slide/verify', { point: `${x},${y}`, captcha_id: state.slide.id })
      state.slide = { ...state.slide, ok: !!r.captcha_verified, msg: r.captcha_verified ? '✅ 验证通过' : `❌ ${r.message || '验证失败'}` }
      renderCards()
      if (!r.captcha_verified) { reset(); loadSlide() }
    },
    refresh: loadSlide,
    close: () => {}
  }
  const rotateEvents = {
    confirm: async (angle, reset) => {
      const r = await postForm('/captcha/rotate/verify', { angle: String(angle), captcha_id: state.rotate.id })
      state.rotate = { ...state.rotate, ok: !!r.captcha_verified, msg: r.captcha_verified ? '✅ 验证通过' : `❌ ${r.message || '验证失败'}` }
      renderCards()
      if (!r.captcha_verified) { reset(); loadRotate() }
    },
    refresh: loadRotate,
    close: () => {}
  }

  function renderCards() {
    const root = document.getElementById('root')
    root.innerHTML = `
      <h1>go-captcha-py × Solid Demo</h1>
      <div class="grid">
        <section class="card"><h2>① 点击验证码（文字）</h2><div id="c1"></div><p class="result ${state.click.ok ? 'ok' : 'fail'}">${state.click.msg}</p></section>
        <section class="card"><h2>② 滑动拼图验证码</h2><div id="c2"></div><p class="result ${state.slide.ok ? 'ok' : 'fail'}">${state.slide.msg}</p></section>
        <section class="card"><h2>③ 旋转验证码</h2><div id="c3"></div><p class="result ${state.rotate.ok ? 'ok' : 'fail'}">${state.rotate.msg}</p></section>
      </div>
      <style>
        body { margin:0; background:#f4f6fa; font-family:-apple-system,'PingFang SC',sans-serif; }
        #root { max-width:1100px; margin:0 auto; padding:24px 16px 60px; }
        h1 { font-size:22px; }
        .grid { display:grid; grid-template-columns:repeat(auto-fill,minmax(340px,1fr)); gap:16px; }
        .card { background:#fff; border-radius:12px; padding:16px; box-shadow:0 2px 8px rgba(0,0,0,.06); }
        .card h2 { font-size:15px; margin:0 0 12px; }
        .result { font-size:13px; margin:10px 0 0; }
        .ok { color:#16a34a; } .fail { color:#dc2626; }
        .gc-loading { display:none !important; } /* upstream spinner bug */
      </style>
    `
    if (state.click.image) {
      render(() => <GoCaptcha.Click data={{ image: state.click.image, thumb: state.click.thumb }} events={clickEvents} config={{ width: 300, height: 220, title: '请依次点击', buttonText: '确认' }} />, document.getElementById('c1'))
    }
    if (state.slide.image) {
      render(() => <GoCaptcha.Slide data={{ image: state.slide.image, thumb: state.slide.thumb, thumbX: state.slide.tx, thumbY: state.slide.ty, thumbWidth: state.slide.tw, thumbHeight: state.slide.th }} events={slideEvents} />, document.getElementById('c2'))
    }
    if (state.rotate.image) {
      render(() => <GoCaptcha.Rotate data={{ image: state.rotate.image, thumb: state.rotate.thumb, thumbSize: state.rotate.thumbSize }} config={{ size: state.rotate.size }} events={rotateEvents} />, document.getElementById('c3'))
    }
  }

  renderCards()
  loadClick(); loadSlide(); loadRotate()
}

render(App, document.getElementById('root'))
