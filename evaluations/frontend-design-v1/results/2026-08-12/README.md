# Frontend Design v1 result

Decision: `evaluated_no_go`. The pinned Full Skill did not beat either pre-frozen control, so it remains undiscoverable and disabled.

- [Blind review and unblinded scores](blind-review.md)
- `raw-artifacts.tar.gz`: all nine implementations, arm traces, 18 desktop/mobile captures, browser result JSON, and the anonymization map.

The raw archive deliberately has no extra receipt/hash ceremony; Git identifies the exact artifact. It is retained because the registry’s controlled-evaluation protocol requires inspectable raw outcomes, not because ordinary delivery should archive screenshots.

## Browser evidence

The recorded run used `puppeteer-core@24.37.5` and `HeadlessChrome/149.0.7827.0`. All nine named interactions passed; all pages rendered meaningful content without console/page errors. Strong no-Skill cold-chain had the only acceptance regression: horizontal overflow at 390 px.

To rerun against an available Chrome/Chromium executable:

```sh
evaluation_root="$(mktemp -d)"
browser_runtime="$(mktemp -d)"
tar -xzf evaluations/frontend-design-v1/results/2026-08-12/raw-artifacts.tar.gz -C "$evaluation_root"
NPM_CONFIG_CACHE="$browser_runtime/npm-cache" npm install --prefix "$browser_runtime" --ignore-scripts --no-save puppeteer-core@24.37.5
CHROMIUM_PATH=/absolute/path/to/chromium \
PUPPETEER_CORE_MODULE="file://$browser_runtime/node_modules/puppeteer-core/lib/esm/puppeteer/puppeteer-core.js" \
node evaluations/frontend-design-v1/verify_browser.mjs "$evaluation_root" "$evaluation_root/recheck"
```

The npm install is evaluation-local and does not alter this repository or the managed Codex runtime.
