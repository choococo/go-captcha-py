import GoCaptcha from 'go-captcha-jslib'
import 'go-captcha-jslib/dist/gocaptcha.global.css'

const b64 = (raw, png) => (raw.startsWith('data:') ? raw : `data:image/${png ? 'png' : 'jpeg'};base64,${raw}`)

async function postForm(url, data) {
  const res = await fetch(url, { method: 'POST', body: new URLSearchParams(data) })
  if (res.status === 403) return { code: 1, captcha_verified: false, message: '已过期' }
  return res.json()
}

const setMsg = (id, ok, msg) => {
  const el = document.getElementById(id)
  el.textContent = msg
  el.className = `result ${ok ? 'ok' : 'fail'}`
}

// ---------------- Click ----------------
const clickCapt = new GoCaptcha.Click({ width: 300, height: 220, title: '请依次点击', buttonText: '确认' })
clickCapt.mount(document.getElementById('c1'))
let clickId = ''

async function loadClick() {
  const r = await (await fetch('/captcha/click')).json()
  clickId = r.captcha_id
  clickCapt.setData({ image: b64(r.image_base64), thumb: b64(r.thumb_base64, true) })
  setMsg('m1', false, '请依次点击文字')
}
clickCapt.setEvents({
  click() {},
  async confirm(dots, reset) {
    const r = await postForm('/captcha/click/verify', {
      dots: dots.map(p => `${p.x},${p.y}`).join(';'),
      captcha_id: clickId
    })
    setMsg('m1', !!r.captcha_verified, r.captcha_verified ? '✅ 验证通过' : `❌ ${r.message || '验证失败'}`)
    if (!r.captcha_verified) { reset(); loadClick() }
  },
  refresh: loadClick,
  close() {}
})

// ---------------- Slide ----------------
const slideCapt = new GoCaptcha.Slide({ width: 300, height: 220 })
slideCapt.mount(document.getElementById('c2'))
let slideId = ''

function loadSlide() {
  fetch('/captcha/slide').then(r => r.json()).then(r => {
    slideId = r.captcha_id
    const img = new Image()
    img.onload = () => {
      slideCapt.setData({
        image: b64(r.image_base64),
        thumb: b64(r.tile_base64, true),
        thumbX: r.tile_x, thumbY: r.tile_y,
        thumbWidth: img.width, thumbHeight: img.height
      })
      setMsg('m2', false, '拖动滑块完成拼图')
    }
    img.src = b64(r.tile_base64, true)
  })
}
slideCapt.setEvents({
  async confirm({ x, y }, reset) {
    const r = await postForm('/captcha/slide/verify', { point: `${x},${y}`, captcha_id: slideId })
    setMsg('m2', !!r.captcha_verified, r.captcha_verified ? '✅ 验证通过' : `❌ ${r.message || '验证失败'}`)
    if (!r.captcha_verified) { reset(); loadSlide() }
  },
  refresh: loadSlide,
  close() {}
})

// ---------------- Rotate ----------------
const rotateCapt = new GoCaptcha.Rotate({ width: 220, height: 220, size: 220 })
rotateCapt.mount(document.getElementById('c3'))
let rotateId = ''

async function loadRotate() {
  const r = await (await fetch('/captcha/rotate')).json()
  rotateId = r.captcha_id
  rotateCapt.setData({ image: b64(r.image_base64, true), thumb: b64(r.thumb_base64, true), thumbSize: r.thumb_size || 150 })
  rotateCapt.setConfig({ width: 220, height: 220, size: r.size || 220 })
  setMsg('m3', false, '旋转图片至正确角度')
}
rotateCapt.setEvents({
  async confirm(angle, reset) {
    const r = await postForm('/captcha/rotate/verify', { angle: String(angle), captcha_id: rotateId })
    setMsg('m3', !!r.captcha_verified, r.captcha_verified ? '✅ 验证通过' : `❌ ${r.message || '验证失败'}`)
    if (!r.captcha_verified) { reset(); loadRotate() }
  },
  refresh: loadRotate,
  close() {}
})

loadClick(); loadSlide(); loadRotate()


// go-captcha-jslib@1.0.9 bug: .gc-loading spinner never hides after load.
const _s = document.createElement('style')
_s.textContent = '.gc-loading { display: none !important; }'
document.head.appendChild(_s)
