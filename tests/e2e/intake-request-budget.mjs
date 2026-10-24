import { createRequire } from "node:module";
const load = createRequire(import.meta.url);
const { chromium } = load(process.env.PLAYWRIGHT_MODULE || "playwright");
const browser = await chromium.launch({ channel: "chrome", headless: true });
try {
  const page = await browser.newPage();
  const counts = { preview: 0, create: 0, analyze: 0 };
  const headers = { "access-control-allow-origin": "*" };
  await page.route("**/api/v1/**", async route => {
    const path = new URL(route.request().url()).pathname;
    if (path === "/api/v1/nlp/analyze") counts.preview++;
    if (path === "/api/v1/matters") {
      counts.create++;
      await new Promise(resolve => setTimeout(resolve, 250));
      return route.fulfill({ json: { id: "fixture-only", revision: 1 }, headers });
    }
    if (path.endsWith("/analyze")) counts.analyze++;
    return route.fulfill({ status: 503, json: { detail: "Fixture: retry is available" }, headers });
  });
  await page.goto(process.env.BASE_URL || "http://127.0.0.1:3000");
  const input = page.locator("#situation");
  await input.fill("I drove my car at 150 km/h");
  await page.waitForTimeout(700);
  await input.fill("I drove my car at 150 km/h on the highway");
  await page.waitForTimeout(700);
  if (counts.preview || counts.create || counts.analyze) throw Error("Typing started backend work");
  await input.evaluate(el => {
    const form = el.closest("form");
    form.dispatchEvent(new Event("submit", { bubbles: true, cancelable: true }));
    form.dispatchEvent(new Event("submit", { bubbles: true, cancelable: true }));
  });
  await page.getByRole("alert").filter({ hasText: "Fixture: retry is available" }).waitFor();
  if (counts.preview !== 0 || counts.create !== 1 || counts.analyze !== 1) throw Error(JSON.stringify(counts));
  await page.getByRole("button", { name: "Understand My Situation", exact: true }).click();
  await page.waitForFunction(() => document.querySelector('[role="alert"]')?.textContent?.includes("Fixture: retry is available"));
  if (counts.create !== 2 || counts.analyze !== 2) throw Error("Retry was lost or duplicated");
  console.log(JSON.stringify({ passed: true, counts, assertions: ["No preview while typing", "Rapid double submit creates one analysis", "Failure releases submit lock for retry"], fixtures: true }));
} finally { await browser.close(); }
