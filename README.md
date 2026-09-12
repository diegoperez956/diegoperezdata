# diegoperezdata

Personal site at https://diegoperezdata.com. Plain HTML, CSS, and JavaScript. GitHub Pages publishes `main`; no build step or runtime dependencies.

## Preview

```sh
python3 -m http.server 8000
```

Open http://localhost:8000. Content, styles, and navigation live in `index.html`.

`selfie.png` is the headshot and social-share image. Any replacement portrait needs visual approval before deployment.

## Browser checks

Playwright is a development-only dependency. Install it in a virtual environment, then run:

```sh
python -m pip install playwright
python -m playwright install chromium
python tests/smoke.py
```

Checks navigation, keyboard controls, touch, PDF previews, local assets, storage failures, and 60 route/viewport combinations. Power BI responses are stubbed; the checks do not validate Microsoft's dashboards. Screenshots and results go to a temporary directory printed at the end.

Design constraints are in `PRODUCT.md` and `DESIGN.md`.
