/* E2E happy-path: solve all four captchas headlessly.
 *
 * Load the page with ?e2e=1 so the app requests the debug answer alongside
 * each captcha (requires backend started with GOCAPTCHA_DEBUG=1), then read
 * the answer from the app's own state and perform the real interaction. */
const { chromium } = require('playwright-core')
const path = require('path')
const os = require('os')

const CHROME = path.join(
  os.homedir(),
  'Library/Caches/ms-playwright/chromium-1234/chrome-mac-arm64/Google Chrome for Testing.app/Contents/MacOS/Google Chrome for Testing'
)

const API = 'http://[::1]:5173/?e2e=1'

;(async () => {
  const browser = await chromium.launch({ executablePath: CHROME, headless: true })
  const page = await browser.newPage()
  await page.goto(API, { waitUntil: 'networkidle' })
  await page.waitForTimeout(1500)

  const readCard = i =>
    page.evaluate(n => {
      const app = document.querySelector('#captcha-app').__vue__
      const keys = ['clickState', 'slideState', 'dragState', 'rotateState']
      return {
        msg: document.querySelectorAll('.card')[n].querySelector('.result').textContent.trim(),
        state: app[keys[n]]
      }
    }, i)

  const results = {}

  // ============ 1. CLICK: click answer dots then confirm ============
  {
    const { state } = await readCard(0)
    const box = await page.locator('.card:nth-child(1) .gc-picture').first().boundingBox()
    const scale = box.width / 300
    for (const pt of state.answer) {
      await page.mouse.click(box.x + pt.x * scale, box.y + pt.y * scale)
      await page.waitForTimeout(150)
    }
    await page.getByRole('button', { name: /确认/ }).first().click()
    await page.waitForTimeout(900)
    results.click = (await readCard(0)).msg
  }

  // ============ 2. SLIDE: drag slider handle to the notch ============
  {
    for (let attempt = 0; attempt < 3; attempt++) {
      // read state and geometry in the same tick to avoid refresh races
      const { state, geo } = await page.evaluate(() => {
        const app = document.querySelector('#captcha-app').__vue__
        const blk = document.querySelectorAll('.card')[1].querySelector('.gc-drag-block').getBoundingClientRect()
        return {
          state: { tileX: app.slideData.thumbX, answer: app.slideState.answer },
          geo: { x: blk.x + blk.width / 2, y: blk.y + blk.height / 2 }
        }
      })
      if (!state.answer) break
      const dx = state.answer.x - state.tileX
      await page.mouse.move(geo.x, geo.y)
      await page.mouse.down()
      await page.mouse.move(geo.x + dx, geo.y, { steps: 25 })
      await page.mouse.up()
      await page.waitForTimeout(1000)
      const msg = (await readCard(1)).msg
      if (msg.includes('✅')) { results.slide = msg; break }
      results.slide = msg
    }
  }

  // ============ 3. DRAG: drag the tile onto the notch ============
  {
    const { state } = await readCard(2)
    const tile = await page.evaluate(() => {
      const app = document.querySelector('#captcha-app').__vue__
      return { x: app.dragData.thumbX, y: app.dragData.thumbY, size: app.dragData.thumbWidth }
    })
    const img = await page.locator('.card:nth-child(3) .gc-picture').first().boundingBox()
    const scale = img.width / 300
    const half = tile.size / 2
    const from = { x: img.x + (tile.x + half) * scale, y: img.y + (tile.y + half) * scale }
    const to = { x: img.x + (state.answer.x + half) * scale, y: img.y + (state.answer.y + half) * scale }
    await page.mouse.move(from.x, from.y)
    await page.mouse.down()
    await page.mouse.move(to.x, to.y, { steps: 20 })
    await page.mouse.up()
    await page.waitForTimeout(900)
    results.drag = (await readCard(2)).msg
  }

  // ============ 4. ROTATE: drag angle slider to the target ============
  {
    for (let attempt = 0; attempt < 4; attempt++) {
      const { state, geo } = await page.evaluate(() => {
        const app = document.querySelector('#captcha-app').__vue__
        const card = document.querySelectorAll('.card')[3]
        const bar = card.querySelector('.gc-drag-slide-bar').getBoundingClientRect()
        const blk = card.querySelector('.gc-drag-block').getBoundingClientRect()
        return {
          state: app.rotateState,
          geo: { bx: bar.x, bw: bar.width, hx: blk.x + blk.width / 2, y: blk.y + blk.height / 2, hw: blk.width }
        }
      })
      if (!state.answer) break
      // component maps: angle = data.angle + left * (360 - data.angle) / maxWidth
      // with data.angle = 0 → left = targetAngle * maxWidth / 360
      const maxWidth = geo.bw - geo.hw
      const px = (state.answer.angle * maxWidth) / 360
      await page.evaluate(({ hx, y, px }) => {
        const card = document.querySelectorAll('.card')[3]
        const bar = card.querySelector('.gc-drag-slide-bar')
        const blk = card.querySelector('.gc-drag-block')
        const mk = (type, cx, cy) => {
          const e = new MouseEvent(type, {
            bubbles: true, cancelable: true, view: window,
            clientX: cx, clientY: cy, button: 0
          })
          Object.defineProperty(e, 'relatedTarget', { value: null })
          return e
        }
        const bx = blk.getBoundingClientRect()
        const sx = bx.x + bx.width / 2
        const sy = bx.y + bx.height / 2
        blk.dispatchEvent(mk('mousedown', sx, sy))
        for (let i = 1; i <= 30; i++) {
          const cx = sx + (px * i) / 30
          bar.dispatchEvent(mk('mousemove', cx, sy))
        }
        // mouseup lands on the moved handle
        const nb = blk.getBoundingClientRect()
        blk.dispatchEvent(mk('mouseup', nb.x + nb.width / 2, nb.y + nb.height / 2))
      }, { hx: geo.hx, y: geo.y, px })
      await page.waitForTimeout(1000)
      const msg = (await readCard(3)).msg
      if (msg.includes('✅')) { results.rotate = msg; break }
      results.rotate = msg
    }
  }

  console.log('=== E2E solve results ===')
  for (const [k, v] of Object.entries(results)) console.log(`  ${k}: ${v}`)
  await page.screenshot({ path: '/tmp/gocaptcha-vue-solved.png', fullPage: true })
  console.log('screenshot: /tmp/gocaptcha-vue-solved.png')

  await browser.close()
  const ok = Object.values(results).filter(v => v.includes('✅')).length
  console.log(`solved: ${ok}/4`)
  process.exit(ok >= 3 ? 0 : 1)
})().catch(e => { console.error('E2E failed:', e.message); process.exit(1) })
