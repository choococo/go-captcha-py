<script>
  import { Click, Slide, Rotate } from 'go-captcha-svelte'

  const b64 = (raw, png) =>
    raw.startsWith('data:') ? raw : `data:image/${png ? 'png' : 'jpeg'};base64,${raw}`

  async function postForm(url, data) {
    const res = await fetch(url, { method: 'POST', body: new URLSearchParams(data) })
    if (res.status === 403) return { code: 1, captcha_verified: false, message: '已过期' }
    return res.json()
  }

  let click = { id: '', image: '', thumb: '', message: '加载中…', ok: false }
  let slide = { id: '', image: '', thumb: '', tx: 0, ty: 0, tw: 0, th: 0, message: '加载中…', ok: false }
  let rotate = { id: '', image: '', thumb: '', size: 220, thumbSize: 150, message: '加载中…', ok: false }

  async function loadClick() {
    const r = await (await fetch('/captcha/click')).json()
    click = { ...click, id: r.captcha_id, image: b64(r.image_base64), thumb: b64(r.thumb_base64, true), message: '请依次点击文字', ok: false }
  }
  function loadSlide() {
    fetch('/captcha/slide').then(r => r.json()).then(r => {
      const img = new Image()
      img.onload = () => { slide = { ...slide, id: r.captcha_id, image: b64(r.image_base64), thumb: b64(r.tile_base64, true), tx: r.tile_x, ty: r.tile_y, tw: img.width, th: img.height, message: '拖动滑块完成拼图', ok: false } }
      img.src = b64(r.tile_base64, true)
    })
  }
  async function loadRotate() {
    const r = await (await fetch('/captcha/rotate')).json()
    rotate = { ...rotate, id: r.captcha_id, image: b64(r.image_base64, true), thumb: b64(r.thumb_base64, true), size: r.size || 220, thumbSize: r.thumb_size || 150, message: '旋转图片至正确角度', ok: false }
  }

  const clickEvents = {
    click: () => {},
    confirm: async (dots, reset) => {
      const r = await postForm('/captcha/click/verify', { dots: dots.map(p => `${p.x},${p.y}`).join(';'), captcha_id: click.id })
      click = { ...click, ok: !!r.captcha_verified, message: r.captcha_verified ? '✅ 验证通过' : `❌ ${r.message || '验证失败'}` }
      if (!r.captcha_verified) { reset(); loadClick() }
    },
    refresh: loadClick,
    close: () => {}
  }
  const slideEvents = {
    confirm: async ({ x, y }, reset) => {
      const r = await postForm('/captcha/slide/verify', { point: `${x},${y}`, captcha_id: slide.id })
      slide = { ...slide, ok: !!r.captcha_verified, message: r.captcha_verified ? '✅ 验证通过' : `❌ ${r.message || '验证失败'}` }
      if (!r.captcha_verified) { reset(); loadSlide() }
    },
    refresh: loadSlide,
    close: () => {}
  }
  const rotateEvents = {
    confirm: async (angle, reset) => {
      const r = await postForm('/captcha/rotate/verify', { angle: String(angle), captcha_id: rotate.id })
      rotate = { ...rotate, ok: !!r.captcha_verified, message: r.captcha_verified ? '✅ 验证通过' : `❌ ${r.message || '验证失败'}` }
      if (!r.captcha_verified) { reset(); loadRotate() }
    },
    refresh: loadRotate,
    close: () => {}
  }

  loadClick(); loadSlide(); loadRotate()
</script>

<main>
  <h1>go-captcha-py × Svelte Demo</h1>
  <div class="grid">
    <section class="card">
      <h2>① 点击验证码（文字）</h2>
      {#if click.image}
        <Click data={{ image: click.image, thumb: click.thumb }} events={clickEvents} config={{ width: 300, height: 220, title: '请依次点击', buttonText: '确认' }} />
      {/if}
      <p class="result" class:ok={click.ok} class:fail={!click.ok}>{click.message}</p>
    </section>
    <section class="card">
      <h2>② 滑动拼图验证码</h2>
      {#if slide.image}
        <Slide data={{ image: slide.image, thumb: slide.thumb, thumbX: slide.tx, thumbY: slide.ty, thumbWidth: slide.tw, thumbHeight: slide.th }} events={slideEvents} />
      {/if}
      <p class="result" class:ok={slide.ok} class:fail={!slide.ok}>{slide.message}</p>
    </section>
    <section class="card">
      <h2>③ 旋转验证码</h2>
      {#if rotate.image}
        <Rotate data={{ image: rotate.image, thumb: rotate.thumb, thumbSize: rotate.thumbSize }} config={{ size: rotate.size }} events={rotateEvents} />
      {/if}
      <p class="result" class:ok={rotate.ok} class:fail={!rotate.ok}>{rotate.message}</p>
    </section>
  </div>
</main>

<style>
  main { max-width: 1100px; margin: 0 auto; padding: 24px 16px 60px; font-family: -apple-system, 'PingFang SC', sans-serif; }
  h1 { font-size: 22px; }
  .grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(340px, 1fr)); gap: 16px; }
  .card { background: #fff; border-radius: 12px; padding: 16px; box-shadow: 0 2px 8px rgba(0,0,0,.06); }
  .card h2 { font-size: 15px; margin: 0 0 12px; }
  .result { font-size: 13px; margin: 10px 0 0; }
  .ok { color: #16a34a; }
  .fail { color: #dc2626; }
  /* upstream bug: spinner never hides, covers center glyphs */
  :global(.gc-loading) { display: none !important; }
</style>
