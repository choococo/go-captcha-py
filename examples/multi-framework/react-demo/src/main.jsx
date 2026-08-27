import React, { useEffect, useState, useCallback } from 'react'
import { createRoot } from 'react-dom/client'
import GoCaptcha from 'go-captcha-react'
import 'go-captcha-react/dist/go-captcha-react.cjs.development.css'

const b64Url = raw => (raw.startsWith('data:') ? raw : `data:image/jpeg;base64,${raw}`)
const b64UrlPng = raw => (raw.startsWith('data:') ? raw : `data:image/png;base64,${raw}`)

async function postForm(url, data) {
  const body = new URLSearchParams(data)
  const res = await fetch(url, { method: 'POST', body })
  if (res.status === 403) return { code: 1, captcha_verified: false, message: '已过期，请刷新' }
  return res.json()
}

function Card({ title, children, message, ok }) {
  return (
    <section className="card">
      <h2>{title}</h2>
      {children}
      <p className={`result ${ok ? 'ok' : 'fail'}`}>{message}</p>
    </section>
  )
}

function App() {
  const [click, setClick] = useState({ id: '', image: '', thumb: '', message: '加载中…', ok: false })
  const [slide, setSlide] = useState({ id: '', image: '', thumb: '', tx: 0, ty: 0, tw: 0, th: 0, message: '加载中…', ok: false })
  const [rotate, setRotate] = useState({ id: '', image: '', thumb: '', size: 220, thumbSize: 150, message: '加载中…', ok: false })

  const loadClick = useCallback(async () => {
    const r = await (await fetch('/captcha/click')).json()
    setClick(s => ({ ...s, id: r.captcha_id, image: b64Url(r.image_base64), thumb: b64UrlPng(r.thumb_base64), message: '请依次点击文字', ok: false }))
  }, [])
  const loadSlide = useCallback(async () => {
    const r = await (await fetch('/captcha/slide')).json()
    const img = new Image()
    img.onload = () => setSlide(s => ({ ...s, id: r.captcha_id, image: b64Url(r.image_base64), thumb: b64UrlPng(r.tile_base64), tx: r.tile_x, ty: r.tile_y, tw: img.width, th: img.height, message: '拖动滑块完成拼图', ok: false }))
    img.src = b64UrlPng(r.tile_base64)
  }, [])
  const loadRotate = useCallback(async () => {
    const r = await (await fetch('/captcha/rotate')).json()
    setRotate(s => ({ ...s, id: r.captcha_id, image: b64UrlPng(r.image_base64), thumb: b64UrlPng(r.thumb_base64), size: r.size || 220, thumbSize: r.thumb_size || 150, message: '旋转图片至正确角度', ok: false }))
  }, [])

  useEffect(() => { loadClick(); loadSlide(); loadRotate() }, [loadClick, loadSlide, loadRotate])

  const clickEvents = {
    click: () => {},
    confirm: async (dots, reset) => {
      const r = await postForm('/captcha/click/verify', { dots: dots.map(p => `${p.x},${p.y}`).join(';'), captcha_id: click.id })
      setClick(s => ({ ...s, ok: !!r.captcha_verified, message: r.captcha_verified ? '✅ 验证通过' : `❌ ${r.message || '验证失败'}` }))
      if (!r.captcha_verified) { reset(); loadClick() }
    },
    refresh: loadClick,
    close: () => {}
  }
  const slideEvents = {
    confirm: async ({ x, y }, reset) => {
      const r = await postForm('/captcha/slide/verify', { point: `${x},${y}`, captcha_id: slide.id })
      setSlide(s => ({ ...s, ok: !!r.captcha_verified, message: r.captcha_verified ? '✅ 验证通过' : `❌ ${r.message || '验证失败'}` }))
      if (!r.captcha_verified) { reset(); loadSlide() }
    },
    refresh: loadSlide,
    close: () => {}
  }
  const rotateEvents = {
    confirm: async (angle, reset) => {
      const r = await postForm('/captcha/rotate/verify', { angle: String(angle), captcha_id: rotate.id })
      setRotate(s => ({ ...s, ok: !!r.captcha_verified, message: r.captcha_verified ? '✅ 验证通过' : `❌ ${r.message || '验证失败'}` }))
      if (!r.captcha_verified) { reset(); loadRotate() }
    },
    refresh: loadRotate,
    close: () => {}
  }

  return (
    <div id="app">
      <h1>go-captcha-py × React Demo</h1>
      <div className="grid">
        <Card title="① 点击验证码（文字）" message={click.message} ok={click.ok}>
          {click.image && <GoCaptcha.Click data={{ image: click.image, thumb: click.thumb }} events={clickEvents} config={{ width: 300, height: 220, title: '请依次点击', buttonText: '确认' }} />}
        </Card>
        <Card title="② 滑动拼图验证码" message={slide.message} ok={slide.ok}>
          {slide.image && <GoCaptcha.Slide data={{ image: slide.image, thumb: slide.thumb, thumbX: slide.tx, thumbY: slide.ty, thumbWidth: slide.tw, thumbHeight: slide.th }} events={slideEvents} />}
        </Card>
        <Card title="③ 旋转验证码" message={rotate.message} ok={rotate.ok}>
          {rotate.image && <GoCaptcha.Rotate data={{ image: rotate.image, thumb: rotate.thumb, thumbSize: rotate.thumbSize }} config={{ size: rotate.size }} events={rotateEvents} />}
        </Card>
      </div>
    </div>
  )
}

createRoot(document.getElementById('root')).render(<App />)


/* go-captcha-react@1.0.5 bug: .gc-loading spinner never hides after the
   image loads and stays overlaid center (z-index:1), covering characters. */
const style = document.createElement('style')
style.textContent = '.gc-loading { display: none !important; }'
document.head.appendChild(style)
