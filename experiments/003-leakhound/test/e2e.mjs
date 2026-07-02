// 漏钱侦探端到端测试（产品本身零依赖；测试需要 playwright-core + Chromium）
// 运行：node test/e2e.mjs [chromium路径]
import { chromium } from "playwright-core";
import { fileURLToPath } from "url";
import path from "path";
import assert from "assert";

const here = path.dirname(fileURLToPath(import.meta.url));
const page_url = "file://" + path.join(here, "..", "index.html");
const exe = process.argv[2] || process.env.CHROMIUM || "/opt/pw-browsers/chromium";

let passed = 0;
function ok(cond, name) {
  assert(cond, name);
  passed++;
  console.log("  ✓ " + name);
}

const browser = await chromium.launch({ executablePath: exe, args: ["--no-sandbox"] });
const page = await browser.newPage({ viewport: { width: 1280, height: 1200 } });

// —— 隐私承诺是可断言的:除页面本身外不允许任何请求 ——
const requests = [];
page.on("request", r => requests.push(r.url()));

console.log("· 示例数据流程");
await page.goto(page_url);
await page.click("#demo");
await page.waitForSelector("#results:not(.hidden)");

const tiles = await page.textContent("#tiles");
ok(/一年流走/.test(tiles), "英雄数字:年化漏钱");
ok(/每月订阅支出/.test(tiles), "月度订阅支出瓦片");
const subsText = await page.textContent("#subs");
ok(subsText.includes("爱奇艺自动续费"), "检出月付订阅(爱奇艺)");
ok(/涨价 20%/.test(subsText), "检出涨价 25→30 (+20%)");
ok(subsText.includes("iCloud 云储存"), "检出 iCloud");
ok(subsText.includes("Spotify Premium") && subsText.includes("已停止"), "Spotify 标记已停止");
ok(subsText.includes("云服务器续费") && subsText.includes("年付"), "检出年付");
ok(!subsText.includes("瑞幸咖啡"), "高频但金额乱跳的消费(瑞幸)不算订阅");
ok(!subsText.includes("某某科技"), "收入不进入订阅表");
ok(await page.$("#chart svg") !== null, "图表渲染");
const rowCount = await page.$$eval("#chartdata tr", rs => rs.length);
ok(rowCount === 19, `图表数据表 18 个月 + 表头 (实际 ${rowCount})`);

// 悬停提示
const bbox = await (await page.$("#chart svg")).boundingBox();
await page.mouse.move(bbox.x + bbox.width * 0.7, bbox.y + bbox.height * 0.5);
ok(await page.isVisible("#charttip"), "悬停出现提示框");
ok(/订阅扣款/.test(await page.textContent("#charttip")), "提示框含双系列读数");

await page.screenshot({ path: process.env.SHOT || "/tmp/leakhound-demo.png", fullPage: true });

console.log("· 银行 CSV(负数=支出,含涨价)");
await page.goto(page_url);
await page.setInputFiles("#file", path.join(here, "fixtures", "bank.csv"));
await page.waitForSelector("#results:not(.hidden)");
let t = await page.textContent("#subs");
ok(t.includes("NETFLIX.COM"), "检出 NETFLIX 月付");
ok(/涨价 7%/.test(t), "检出 55→59 涨价(+7%)");
ok(!t.includes("SALARY"), "工资(正数)不误判");
let files = await page.textContent("#files");
ok(/UTF-8/.test(files), "编码识别 UTF-8");

console.log("· 支付宝格式(GBK 编码,收/支列,带表头前言)");
await page.goto(page_url);
await page.setInputFiles("#file", path.join(here, "fixtures", "alipay_gbk.csv"));
await page.waitForSelector("#results:not(.hidden)");
t = await page.textContent("#subs");
ok(t.includes("哔哩哔哩大会员"), "GBK 解码 + 前言跳过 + 检出月付");
files = await page.textContent("#files");
ok(/GBK/.test(files), "编码识别 GBK");
ok(/排除收入\/退款等 2 笔/.test(files), "收入与退款被排除");

console.log("· 隐私:零网络请求");
const external = requests.filter(u => !u.startsWith("file://"));
ok(external.length === 0, `所有请求均为本地 file:// (共 ${requests.length} 个,外部 0 个)`);

await browser.close();
console.log(`\n全部通过:${passed} 项断言 ✓`);
