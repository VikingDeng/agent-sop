# Frozen experiment-run application

This is the starting repository for `out_product_02`. It is intentionally a
real but poor product: the API and experiment semantics work, while the UI is
a generic gradient/card page that only handles the happy path.

Run it with:

```bash
python3 app.py --port 8765
```

Then open `http://127.0.0.1:8765`. The server uses only the Python standard
library. Set `EXPERIMENT_DATA_DIR` to a writable copy of `data/` when running
tests or an evaluation; the checked-in fixture must remain unchanged.

The public API is frozen by `api-contract.json`. A redesign may change the
information architecture and all files under `static/`, but it must preserve
the API, experiment meanings, and fixture scenarios. The starting UI does not
correctly expose creation, progress, failure diagnosis, empty/error/loading
states, long logs, or a narrow-screen layout. Those statements identify test
surfaces, not a preferred design answer.
