# 001 · 字种 · Seed Words

**念头**：一句话确定性地长成一幅画。语言变成图像。

打开 [`index.html`](index.html)，输入任何一句话，回车。
这句话会被哈希成这幅画的全部参数：色系、明暗、流场的走向、粒子的数量——
并且句中每一个字符都会在画布上投下一个属于自己的涡旋。
句子越长，画面越纷繁；同一句话，永远长出同一幅画。

Open `index.html`, type any phrase, press Enter. The phrase is hashed into
every parameter of the painting — palette, flow field, particle count — and
each character casts its own vortex onto the canvas. Longer sentences grow
busier paintings; the same words always grow the same one.

## 细节 · Details

- **确定性** — 动画按固定步数（1500 步）推进而不是按时间，所以同一句话在任何机器上都长成同一幅画。画会「完成」：停笔之后自动落款。
- **可分享** — 句子编码在 URL 的 `#` 里，链接即作品。
- **零依赖** — 单个 HTML 文件，没有框架，没有网络请求。
- 哈希用 cyrb128，随机数用 sfc32，流场是若干平面波的叠加，加上每个字符一个高斯衰减的切向涡旋。

## 用法 · Usage

```
open index.html          # 直接用浏览器打开即可
```

回车重新播种；「保存 PNG」把完成的画（含落款）存下来。
