import { Component, OnInit } from '@angular/core';

const b64 = (raw: string, png = false) =>
  raw.startsWith('data:') ? raw : `data:image/${png ? 'png' : 'jpeg'};base64,${raw}`;

async function postForm(url: string, data: Record<string, string>) {
  const res = await fetch(url, { method: 'POST', body: new URLSearchParams(data) });
  if (res.status === 403) return { code: 1, captcha_verified: false, message: '已过期' };
  return res.json();
}

@Component({
  selector: 'app-root',
  standalone: false,
  template: `
    <h1>go-captcha-py × Angular Demo</h1>
    <div class="grid">
      <section class="card">
        <h2>① 点击验证码（文字）</h2>
        <go-captcha-click *ngIf="clickData.image" [config]="clickConfig" [data]="clickData" [events]="clickEvents"></go-captcha-click>
        <p class="result" [class.ok]="clickOk" [class.fail]="!clickOk">{{ clickMsg }}</p>
      </section>
      <section class="card">
        <h2>② 滑动拼图验证码</h2>
        <go-captcha-slide *ngIf="slideData.image" [data]="slideData" [events]="slideEvents"></go-captcha-slide>
        <p class="result" [class.ok]="slideOk" [class.fail]="!slideOk">{{ slideMsg }}</p>
      </section>
      <section class="card">
        <h2>③ 旋转验证码</h2>
        <go-captcha-rotate *ngIf="rotateData.image" [config]="rotateConfig" [data]="rotateData" [events]="rotateEvents"></go-captcha-rotate>
        <p class="result" [class.ok]="rotateOk" [class.fail]="!rotateOk">{{ rotateMsg }}</p>
      </section>
    </div>
  `,
  styles: [`
    :host { display: block; max-width: 1100px; margin: 0 auto; padding: 24px 16px 60px; font-family: -apple-system, 'PingFang SC', sans-serif; }
    h1 { font-size: 22px; }
    .grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(340px, 1fr)); gap: 16px; }
    .card { background: #fff; border-radius: 12px; padding: 16px; box-shadow: 0 2px 8px rgba(0,0,0,.06); }
    .card h2 { font-size: 15px; margin: 0 0 12px; }
    .result { font-size: 13px; margin: 10px 0 0; }
    .ok { color: #16a34a; } .fail { color: #dc2626; }
    /* upstream spinner bug: never hides, covers center glyphs */
    ::ng-deep .gc-loading { display: none !important; }
  `]
})
export class AppComponent implements OnInit {
  clickId = '';
  clickData: any = { image: '', thumb: '' };
  clickConfig: any = { width: 300, height: 220, title: '请依次点击', buttonText: '确认' };
  clickMsg = '加载中…';
  clickOk = false;

  slideId = '';
  slideData: any = { image: '', thumb: '', thumbX: 0, thumbY: 0, thumbWidth: 0, thumbHeight: 0 };
  slideMsg = '加载中…';
  slideOk = false;

  rotateId = '';
  rotateData: any = { image: '', thumb: '', thumbSize: 150 };
  rotateConfig: any = { size: 220 };
  rotateMsg = '加载中…';
  rotateOk = false;

  clickEvents: any = {
    click: () => {},
    confirm: async (dots: any[], reset: () => void) => {
      const r = await postForm('/captcha/click/verify', {
        dots: dots.map(p => `${p.x},${p.y}`).join(';'),
        captcha_id: this.clickId
      });
      this.clickOk = !!r.captcha_verified;
      this.clickMsg = r.captcha_verified ? '✅ 验证通过' : `❌ ${r.message || '验证失败'}`;
      if (!r.captcha_verified) { reset(); this.loadClick(); }
    },
    refresh: () => this.loadClick(),
    close: () => {}
  };

  slideEvents: any = {
    confirm: async ({ x, y }: { x: number; y: number }, reset: () => void) => {
      const r = await postForm('/captcha/slide/verify', { point: `${x},${y}`, captcha_id: this.slideId });
      this.slideOk = !!r.captcha_verified;
      this.slideMsg = r.captcha_verified ? '✅ 验证通过' : `❌ ${r.message || '验证失败'}`;
      if (!r.captcha_verified) { reset(); this.loadSlide(); }
    },
    refresh: () => this.loadSlide(),
    close: () => {}
  };

  rotateEvents: any = {
    confirm: async (angle: number, reset: () => void) => {
      const r = await postForm('/captcha/rotate/verify', { angle: String(angle), captcha_id: this.rotateId });
      this.rotateOk = !!r.captcha_verified;
      this.rotateMsg = r.captcha_verified ? '✅ 验证通过' : `❌ ${r.message || '验证失败'}`;
      if (!r.captcha_verified) { reset(); this.loadRotate(); }
    },
    refresh: () => this.loadRotate(),
    close: () => {}
  };

  ngOnInit() { this.loadClick(); this.loadSlide(); this.loadRotate(); }

  async loadClick() {
    const r = await (await fetch('/captcha/click')).json();
    this.clickId = r.captcha_id;
    this.clickData = { image: b64(r.image_base64), thumb: b64(r.thumb_base64, true) };
    this.clickMsg = '请依次点击文字';
  }

  loadSlide() {
    fetch('/captcha/slide').then(r => r.json()).then(r => {
      this.slideId = r.captcha_id;
      const img = new Image();
      img.onload = () => {
        this.slideData = {
          image: b64(r.image_base64), thumb: b64(r.tile_base64, true),
          thumbX: r.tile_x, thumbY: r.tile_y, thumbWidth: img.width, thumbHeight: img.height
        };
        this.slideMsg = '拖动滑块完成拼图';
      };
      img.src = b64(r.tile_base64, true);
    });
  }

  async loadRotate() {
    const r = await (await fetch('/captcha/rotate')).json();
    this.rotateId = r.captcha_id;
    this.rotateData = { image: b64(r.image_base64, true), thumb: b64(r.thumb_base64, true), thumbSize: r.thumb_size || 150 };
    this.rotateConfig = { size: r.size || 220 };
    this.rotateMsg = '旋转图片至正确角度';
  }
}
