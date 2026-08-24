/**
 * Keep the CLEAR-ATS Streamlit dashboard reachable.
 *
 * Streamlit Community Cloud hibernates an app after 12 h without traffic.
 * A plain HTTP GET does NOT count as traffic: it returns the static SPA shell
 * with HTTP 200 while the Python process stays down. The backend only starts
 * when a real browser executes JS and opens the WebSocket to /_stcore/stream,
 * so this script drives headless Chromium.
 *
 * Exit codes: 0 = app is serving; 1 = app could not be brought up.
 */
const { chromium } = require('playwright');

const URL          = process.env.APP_URL;
const TITLE_MATCH  = /CLEAR-ATS/i;   // set by the app's own st.set_page_config
const WAKE_WAIT_MS = 120_000;        // cold start can take 60-120 s
const ATTEMPTS     = 2;

const ERROR_PATTERNS = [
  /error running app/i,
  /installer returned a non-zero exit code/i,
  /oh no\.?\s*error/i,
  /this app has encountered an error/i,
];

async function attempt(browser, n) {
  const ctx  = await browser.newContext({ viewport: { width: 1280, height: 900 } });
  const page = await ctx.newPage();

  let socketOpened = false;
  page.on('websocket', ws => {
    if (ws.url().includes('_stcore/stream')) socketOpened = true;
  });

  console.log(`--- attempt ${n}/${ATTEMPTS} ---`);
  await page.goto(URL, { waitUntil: 'domcontentloaded', timeout: 60_000 });
  await page.waitForTimeout(8_000);

  // Wake it if it is hibernating. Primary selector is the button label;
  // the fallback catches a future relabelling of the same page.
  let wake = page.getByRole('button', { name: /get this app back up/i });
  if (!(await wake.count())) {
    const body = (await page.textContent('body').catch(() => '')) || '';
    if (/gone to sleep/i.test(body)) {
      wake = page.locator('button').first();   // fallback: the sleep page has one button
      console.log('sleep page detected via text; using fallback button selector');
    }
  }
  if (await wake.count()) {
    console.log('state: ASLEEP -> clicking wake button');
    await wake.first().click();
    await page.waitForTimeout(WAKE_WAIT_MS);
  } else {
    console.log('state: already awake');
  }

  // Wait for the Streamlit app frame, then hold the socket open briefly.
  await page.waitForSelector('[data-testid="stApp"]', { timeout: 60_000 }).catch(() => {});
  await page.waitForTimeout(10_000);

  const title = await page.title();
  const body  = ((await page.textContent('body').catch(() => '')) || '').replace(/\s+/g, ' ');
  const asleep = /gone to sleep|get this app back up/i.test(body);
  const appError = ERROR_PATTERNS.find(re => re.test(body));

  console.log('title:               ', title);
  console.log('websocket_established:', socketOpened);
  console.log('still_asleep:        ', asleep);
  if (appError) console.log('app_error_detected:  ', appError.toString());

  await ctx.close();

  if (appError) return { ok: false, reason: `app error page: ${appError}` };
  if (asleep)   return { ok: false, reason: 'still showing the sleep page' };
  if (!TITLE_MATCH.test(title))
    return { ok: false, reason: `title "${title}" does not match ${TITLE_MATCH}` };
  if (!socketOpened)
    return { ok: false, reason: 'no /_stcore/stream websocket was opened' };
  return { ok: true };
}

(async () => {
  if (!URL) { console.error('APP_URL is not set'); process.exit(1); }
  const browser = await chromium.launch(
    process.env.PW_CHANNEL ? { channel: process.env.PW_CHANNEL } : {}   // CI: bundled chromium; local test: PW_CHANNEL=chrome
  );
  let last = { ok: false, reason: 'no attempt ran' };
  for (let i = 1; i <= ATTEMPTS; i++) {
    try {
      last = await attempt(browser, i);
    } catch (e) {
      last = { ok: false, reason: `exception: ${e.message}` };
      console.log('attempt threw:', e.message);
    }
    if (last.ok) break;
    if (i < ATTEMPTS) { console.log('retrying in 30 s...'); await new Promise(r => setTimeout(r, 30_000)); }
  }
  await browser.close();

  if (!last.ok) {
    console.error(`FAILED: ${last.reason}`);
    console.error('The dashboard is not serving. Check the Streamlit Cloud logs at share.streamlit.io.');
    process.exit(1);
  }
  console.log('OK: dashboard is serving.');
})();
