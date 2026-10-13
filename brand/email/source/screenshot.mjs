// Screenshots every rendered email at phone (390px) and desktop (680px) width.
//   cd landing && node ../docs/brand/email/source/screenshot.mjs   (uses landing's Playwright)
import { createRequire } from "node:module";
const { chromium } = createRequire(`${process.cwd()}/package.json`)("@playwright/test");
import { readdirSync, mkdirSync } from "node:fs";
import { resolve, dirname } from "node:path";
import { fileURLToPath } from "node:url";

const root = resolve(dirname(fileURLToPath(import.meta.url)), "..");
mkdirSync(`${root}/previews`, { recursive: true });
const ids = readdirSync(root).filter((f) => f.endsWith(".html") && f !== "index.html").map((f) => f.replace(".html", ""));
const browser = await chromium.launch({ executablePath: process.env.CHROME || undefined });
for (const [suffix, width] of [["", 390], ["-desktop", 680]]) {
  const ctx = await browser.newContext({ viewport: { width, height: 800 }, deviceScaleFactor: 2 });
  const page = await ctx.newPage();
  for (const id of ids) {
    await page.goto(`file://${root}/${id}.html`);
    await page.waitForLoadState("networkidle");
    await page.screenshot({ path: `${root}/previews/${id}${suffix}.png`, fullPage: true });
  }
  await ctx.close();
}
await browser.close();
console.log("shot", ids.length, "emails");
