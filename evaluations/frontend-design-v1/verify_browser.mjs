import fs from "node:fs/promises";
import path from "node:path";
import { pathToFileURL } from "node:url";
const puppeteerModule = process.env.PUPPETEER_CORE_MODULE || "puppeteer-core";
const { default: puppeteer } = await import(puppeteerModule);

const root = process.argv[2];
const outputRoot = process.argv[3];
const chromiumPath = process.env.CHROMIUM_PATH;
if (!root || !outputRoot || !chromiumPath) {
  throw new Error(
    "usage: CHROMIUM_PATH=/path/to/chromium [PUPPETEER_CORE_MODULE=...] " +
    "node verify_browser.mjs <evaluation-root> <output-root>",
  );
}

const arms = ["strong_no_skill", "minimal_reminder", "full_skill"];
const fixtures = ["cold-chain", "cinema", "roastery"];
const viewports = {
  desktop: { width: 1440, height: 1024 },
  mobile: { width: 390, height: 844 },
};

const browser = await puppeteer.launch({
  executablePath: chromiumPath,
  headless: true,
  userDataDir: "/tmp/frontend-design-eval-puppeteer-profile",
  args: [
    "--no-sandbox",
    "--disable-gpu",
    "--single-process",
    "--no-zygote",
    "--disable-dev-shm-usage",
    "--allow-file-access-from-files",
  ],
  env: {
    ...process.env,
    HOME: "/tmp/frontend-design-eval-home",
    XDG_CACHE_HOME: "/tmp/frontend-design-eval-cache",
  },
});
const browserVersion = await browser.version();

const results = [];
async function buttonByText(page, text) {
  const buttons = await page.$$("button");
  for (const button of buttons) {
    const label = await button.evaluate(element => element.textContent.trim());
    if (label.includes(text)) {
      return button;
    }
  }
  throw new Error(`button not found: ${text}`);
}

async function addButtonFor(page, title) {
  const buttons = await page.$$("button.add");
  for (const button of buttons) {
    const context = await button.evaluate(element => element.closest("article")?.innerText || "");
    if (context.toLowerCase().includes(title.toLowerCase())) return button;
  }
  throw new Error(`add control not found for: ${title}`);
}

async function verifyInteraction(page, fixture) {
  if (fixture === "cold-chain") {
    const shipments = await page.$$("button.shipment, button.ship");
    if (shipments.length < 3) throw new Error("cold-chain requires three shipment controls");
    const shipmentByText = async text => {
      for (const shipment of shipments) {
        if ((await shipment.evaluate(element => element.innerText)).includes(text)) return shipment;
      }
      throw new Error(`shipment control not found for: ${text}`);
    };
    let before = await page.evaluate(() => document.querySelector("main")?.innerText || "");
    if (before.includes("4.1°C")) {
      await (await shipmentByText("9.4°C")).click();
      before = await page.evaluate(() => document.querySelector("main")?.innerText || "");
    }
    await (await shipmentByText("4.1°C")).click();
    const after = await page.evaluate(() => document.querySelector("main")?.innerText || "");
    if (before === after || !after.includes("4.1°C")) throw new Error("shipment selection did not update detail");
    await (await shipmentByText("9.4°C")).click();
    await (await buttonByText(page, "Start intervention")).click();
    const passed = await page.evaluate(() => {
      const text = document.body.innerText;
      return /not dispatched|no dispatch|local guidance/i.test(text) &&
        /Call|Contact|Protect|Escalate|operational action/i.test(text);
    });
    if (!passed) throw new Error("intervention did not reveal local operational actions and no-dispatch truth");
    return true;
  }
  if (fixture === "cinema") {
    const totalText = async () => page.evaluate(() =>
      (document.querySelector("#total")?.innerText || document.querySelector(".summary")?.innerText || "").trim()
    );
    await (await addButtonFor(page, "Salt Letters")).click();
    const oneTotal = await totalText();
    await (await addButtonFor(page, "Static Bloom")).click();
    const twoTotal = await totalText();
    if (oneTotal === twoTotal || !/(?:149\s*min|2h\s*29m)/i.test(twoTotal)) {
      throw new Error(`two-film duration did not reach 149 minutes: ${JSON.stringify(twoTotal)}`);
    }
    await (await addButtonFor(page, "The Last Ferry")).click();
    const conflictVisible = await page.evaluate(() => {
      const conflict = document.querySelector("#conflict");
      return Boolean(conflict && getComputedStyle(conflict).display !== "none" && /overlap|runs into|begins before/i.test(conflict.innerText));
    });
    if (!conflictVisible) throw new Error("overlapping film did not reveal conflict");
    const recovery = await page.$("#recover");
    if (!recovery) throw new Error("conflict recovery control missing");
    await recovery.click();
    const recovered = await page.evaluate(() => {
      const conflict = document.querySelector("#conflict");
      return Boolean(conflict && getComputedStyle(conflict).display === "none");
    });
    if (!recovered) throw new Error("conflict recovery did not restore the itinerary");
    return true;
  }
  const initialPanel = await page.evaluate(() =>
    document.querySelector("#curve")?.classList.contains("active") &&
    !document.querySelector("#milestones")?.classList.contains("active")
  );
  if (!initialPanel) throw new Error("Curve was not the initial roastery view");
  await (await buttonByText(page, "Milestones")).click();
  const milestoneVisible = await page.evaluate(() => document.querySelector("#milestones")?.classList.contains("active"));
  if (!milestoneVisible) throw new Error("Milestones view did not activate");
  await (await buttonByText(page, "Curve")).click();
  const curveVisible = await page.evaluate(() => document.querySelector("#curve")?.classList.contains("active"));
  if (!curveVisible) throw new Error("Curve view did not reactivate");
  await (await buttonByText(page, "Release check")).click();
  const releaseButton = await page.$("#releaseBtn");
  if (!releaseButton) throw new Error("roastery release control not found");
  if (await releaseButton.evaluate(button => !button.disabled)) throw new Error("release was enabled before disposition");
  const select = await page.$("select#disp");
  if (select) {
    const values = await select.$$eval("option", options => options.map(option => option.value).filter(Boolean));
    await select.select(values[0]);
    const note = await page.$("textarea#note");
    if (note) await note.type("Frozen evaluation disposition");
    await (await buttonByText(page, "Record disposition")).click();
  } else {
    const radio = await page.$('input[name="disp"]');
    if (!radio) throw new Error("roastery disposition control not found");
    await radio.click();
  }
  const enabled = await releaseButton.evaluate(button => !button.disabled);
  if (!enabled) throw new Error("release remained disabled after disposition");
  await releaseButton.click();
  const persisted = await page.evaluate(() => /local|stored|recorded/i.test(document.body.innerText));
  if (!persisted) throw new Error("release did not expose local/stored truth");
  return true;
}

try {
  for (const arm of arms) {
    for (const fixture of fixtures) {
      const page = await browser.newPage();
      const consoleErrors = [];
      const pageErrors = [];
      page.on("console", message => {
        if (message.type() === "error") consoleErrors.push(message.text());
      });
      page.on("pageerror", error => pageErrors.push(String(error)));
      const source = path.resolve(root, arm, fixture, "index.html");
      await page.goto(pathToFileURL(source).href, { waitUntil: "load" });
      let interactionPassed = false;
      let interactionError = null;
      try {
        interactionPassed = await verifyInteraction(page, fixture);
      } catch (error) {
        interactionError = String(error);
      }

      const captures = {};
      let overflow = false;
      for (const [name, viewport] of Object.entries(viewports)) {
        await page.setViewport(viewport);
        await page.reload({ waitUntil: "load" });
        const destination = path.resolve(outputRoot, arm, `${fixture}-${name}.png`);
        await fs.mkdir(path.dirname(destination), { recursive: true });
        await page.screenshot({ path: destination, fullPage: false });
        const state = await page.evaluate(() => ({
          bodyTextLength: document.body.innerText.trim().length,
          horizontalOverflow:
            document.documentElement.scrollWidth > document.documentElement.clientWidth,
        }));
        captures[name] = { path: destination, ...state };
        overflow ||= state.horizontalOverflow;
      }

      results.push({
        arm,
        fixture,
        title: await page.title(),
        captures,
        consoleErrors,
        pageErrors,
        horizontalOverflow: overflow,
        interactionPassed,
        interactionError,
      });
      await page.close();
    }
  }
} finally {
  await browser.close();
}

await fs.mkdir(outputRoot, { recursive: true });
await fs.writeFile(
  path.resolve(outputRoot, "browser-results.json"),
  JSON.stringify({ browser: browserVersion, results }, null, 2) + "\n",
);

const failures = results.filter(
  item =>
    item.horizontalOverflow ||
    !item.interactionPassed ||
    item.consoleErrors.length ||
    item.pageErrors.length ||
    Object.values(item.captures).some(capture => capture.bodyTextLength === 0),
);
console.log(JSON.stringify({ checked: results.length, failures }, null, 2));
if (failures.length) process.exitCode = 1;
