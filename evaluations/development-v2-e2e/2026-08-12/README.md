# Development Profile v2 complete-product E2E

Decision: positive end-to-end example, not a causal benchmark. A fresh supervisor running the installed Development Profile v2 delivered a complete local cold-chain product instead of a static dashboard or frontend-only prototype.

## Frozen product contract

- single-user, local-only cold-chain operations product;
- shipment manifest and selectable decision detail;
- one legal incident lifecycle: `none → open → acknowledged → resolved`;
- resolution requires a disposition and illegal transitions return explicit non-2xx JSON errors;
- SQLite persistence and process-restart survival;
- append-only audit timeline;
- real browser journey at 1440×1024 and 390×844;
- no auth, containers, CI, external dispatch, hashes, generic framework layer, or speculative integration.

The top-level agent froze and integrated the result. It delegated one stable implementation package to a bounded Luna worker, then independently authored and ran the browser/restart oracle. Actual service-side model/token/WCU attribution was not independently available and remains `[UNCERTAIN]`.

## Independently rerun evidence

- `python3 -m py_compile app.py` and `node --check static/app.js`: passed;
- `python3 -m unittest discover -s tests -v`: 4/4 passed;
- real Chromium journey: no selection → active incident → visible server `409` → missing-disposition feedback → resolved;
- API read-back after the browser action: `resolved`, disposition `held`, 3 audit events;
- a new server process using the same SQLite file returned the same state and audit count;
- desktop/mobile horizontal overflow: 0 px; page errors: 0; unexpected console errors: 0; failed requests: 0;
- desktop and mobile screenshots show the selected shipment, route, temperature exception, resolved disposition, and audit timeline.

[`relay-north-product.tar.gz`](relay-north-product.tar.gz) contains the runnable source, API/domain tests, browser oracle, evidence trace, and four screenshots. Extract it, run `python3 app.py`, and open <http://127.0.0.1:8080>.

## What this establishes

This case shows that v2 can preserve a `complete product` contract through delegation and force evidence across browser → HTTP API → domain transition → SQLite → restart, while avoiding auth, CI, containers, external services, or generic architecture that the contract did not need. It also produced a visibly domain-specific interface rather than the earlier interchangeable card dashboard.

It does **not** establish a universal quality score or prove that v2 alone caused the result: this is one deterministic local product, one top-level generation, one delegated implementation, and one visual reviewer. Broader claims still require diverse controlled tasks.
