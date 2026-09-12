from pathlib import Path
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from threading import Thread
from urllib.parse import urlparse, unquote
import json
from tempfile import mkdtemp
from playwright.sync_api import sync_playwright, expect

ROOT = Path(__file__).resolve().parents[1]
OUT = Path(mkdtemp(prefix='portfolio-smoke-'))

class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, *args): pass

server = ThreadingHTTPServer(('127.0.0.1', 0), partial(QuietHandler, directory=str(ROOT)))
Thread(target=server.serve_forever, daemon=True).start()
base = f'http://127.0.0.1:{server.server_port}'
errors, requests, results = [], [], []

with sync_playwright() as pw:
    browser = pw.chromium.launch(headless=True)
    context = browser.new_context(viewport={'width': 1440, 'height': 1000})
    # Test our iframe markup without relying on third-party Power BI availability.
    context.route('https://**/*', lambda route: route.fulfill(body='<html><title>External embed stub</title></html>', content_type='text/html'))
    page = context.new_page()
    page.on('pageerror', lambda error: errors.append(str(error)))
    page.on('request', lambda request: requests.append(request.url))

    def go(hash=''):
        page.goto(base + '/' + hash, wait_until='domcontentloaded')
        page.locator('#rows a').first.wait_for()
        page.wait_for_timeout(60)

    go()
    expect(page.locator('main img.cover')).to_have_attribute('src', '/portrait.svg')
    assert page.locator('main img.cover').evaluate('(img) => img.complete && img.naturalWidth === 432')
    assert not any(url.endswith('/selfie.png') for url in requests)
    assert page.locator('h1').count() == 1
    page.screenshot(path=str(OUT / 'home-desktop.png'), full_page=True)

    assets = page.evaluate("[...dataViz, ...graphicDesign].flatMap(x => [x.src, x.thumb]).filter(x => x && x.startsWith('/'))")
    for asset in assets + ['/Diego_Perez_Resume.pdf', '/portrait.svg']:
        assert (ROOT / unquote(asset).lstrip('/')).is_file(), asset
        assert context.request.get(base + asset).ok, asset
    results.append('All local project assets and resume resolve')

    routes = ['#/', '#/about', '#/contact', '#/selected-work/polars', '#/selected-work/rym', '#/visual-studies/marcos']
    for width, height in [(320, 740), (375, 812), (390, 844), (768, 1024), (801, 900), (1024, 900), (1200, 900), (1440, 1000), (1920, 1080), (844, 390)]:
        page.set_viewport_size({'width': width, 'height': height})
        for route in routes:
            go(route)
            dims = page.evaluate('({width: innerWidth, scroll: document.documentElement.scrollWidth})')
            assert dims['scroll'] <= dims['width'], (width, height, route, dims)
            if page.locator('.sub-focus').count():
                focus = page.locator('.sub-focus').bounding_box()
                pane = page.locator('#pane').bounding_box()
                assert focus['width'] >= 140, (width, height, route, focus)
                assert focus['x'] + focus['width'] <= pane['x'] + pane['width'] + 1, (width, height, route, focus, pane)
        if width in [390, 1440]:
            page.screenshot(path=str(OUT / f'collection-{width}.png'), full_page=True)
    results.append('60 route/viewport combinations have no page overflow or clipped preview columns')

    page.set_viewport_size({'width': 1440, 'height': 1000})
    go('#/selected-work/polars')
    for col in ['name', 'type', 'date']:
        button = page.locator(f'[data-sort="{col}"]')
        button.focus(); button.press('Enter')
        assert page.evaluate('document.activeElement.dataset.sort') == col
        assert page.locator('#rows .active').get_attribute('data-section') == 'data-viz'
        button.press('Space')
        assert '▼' in button.inner_text()
        sub = page.locator(f'[data-sub-sort="{col}"]')
        sub.focus(); sub.press('Space')
        assert page.evaluate('document.activeElement.dataset.subSort') == col
        sub.press('Enter')
        assert '▼' in sub.inner_text()
    results.append('Native sorting buttons support Enter/Space and retain focus/active navigation')

    page.locator('.sub-row[data-item="alice"]').focus()
    page.locator('.sub-row[data-item="alice"]').press('Enter')
    expect(page).to_have_url(base + '/#/selected-work/alice')
    assert page.locator('.pdf-thumb').locator('..').get_attribute('href').endswith('.pdf')
    page.get_by_role('button', name='view inline').click()
    expect(page.locator('.focus-frame iframe')).to_have_attribute('title', 'ALICE Correlations Presentation')
    page.locator('.focus-frame iframe').evaluate('(node) => node.dataset.instance = "stable"')
    page.locator('.sub-row[data-item="alice"]').hover()
    page.locator('.sub-focus h3').hover()
    expect(page.locator('.focus-frame iframe')).to_have_attribute('data-instance', 'stable')
    page.locator('#rows [data-section="about"] a').hover()
    page.locator('.hint').hover()
    expect(page.locator('.focus-frame iframe')).to_have_attribute('data-instance', 'stable')
    results.append('PDF thumbnails link to files; inline PDFs are labeled and survive repeat hover')

    for item in ['prison', 'atlas']:
        go('#/selected-work/' + item)
        assert page.locator('iframe').get_attribute('title')
    go('#/about')
    page.locator('#rows [data-section="contact"] a').focus()
    page.locator('#rows [data-section="contact"] a').press('Enter')
    expect(page).to_have_url(base + '/#/contact')
    page.go_back()
    expect(page).to_have_url(base + '/#/about')
    page.reload()
    expect(page.locator('.section-title')).to_have_text('about')
    for route in ['#/unknown', '#/constructor', '#/__proto__', '#/%E0%A4%A', '#/selected-work/missing']:
        go(route)
        assert page.locator('#pane').inner_text().strip()
    results.append('Section navigation, history, reload, malformed hashes and unknown items work')

    go()
    page.locator('#mkdir-input').fill('test-folder')
    page.locator('#mkdir-input').press('Enter')
    assert len(page.evaluate("JSON.parse(localStorage.getItem('userDirs'))")) == 1
    go('#/test-folder')
    expect(page.locator('.section-title')).to_have_text('Index of /test-folder')
    page.get_by_role('button', name='rm -rf test-folder/').focus()
    page.get_by_role('button', name='rm -rf test-folder/').press('Space')
    expect(page).to_have_url(base + '/#/')
    page.locator('#mkdir-input').fill('about')
    page.locator('#mkdir-input').press('Enter')
    assert not page.evaluate("JSON.parse(localStorage.getItem('userDirs'))")
    for storage in ['not-json', '{}', '[null, 1, {}, {"name": 7}, {"name":"about","date":"2026-09-12"}]', '[{"name":"x","date":"<img src=x onerror=alert(1)>"}]']:
        page.evaluate('(value) => localStorage.setItem("userDirs", value)', storage)
        page.reload()
        expect(page.locator('main img.cover')).to_be_visible()
    results.append('Folder creation/deletion, reserved names and corrupt localStorage work')

    blocked = browser.new_context()
    blocked.add_init_script("Object.defineProperty(window, 'localStorage', {get() { throw new Error('Storage blocked'); }});")
    bp = blocked.new_page()
    bp.on('pageerror', lambda error: errors.append(str(error)))
    bp.goto(base)
    bp.locator('#mkdir-input').fill('session-only')
    bp.locator('#mkdir-input').press('Enter')
    bp.locator('#rows [data-section="user:session-only"] a').click()
    bp.get_by_role('button', name='rm -rf session-only/').click()
    results.append('Folder gag still works when storage is blocked')

    touch = browser.new_context(viewport={'width': 390, 'height': 844}, is_mobile=True, has_touch=True)
    tp = touch.new_page(); tp.goto(base)
    assert 'tap to open' in tp.locator('.hint').inner_text()
    tp.locator('#rows [data-section="graphic-design"] a').tap()
    tp.locator('.sub-row[data-item="frontera"]').tap()
    expect(tp).to_have_url(base + '/#/visual-studies/frontera')
    results.append('Touch instructions and tap navigation work')

    nojs = browser.new_context(java_script_enabled=False)
    np = nojs.new_page(); np.goto(base)
    expect(np.locator('noscript a').first).to_be_visible()
    results.append('Resume and email remain accessible without JavaScript')

    assert not errors, errors
    browser.close()
server.shutdown()
(OUT / 'results.json').write_text(json.dumps(results, indent=2))
print('\n'.join('PASS: ' + result for result in results))
print('PASS: no uncaught page errors')
print('Screenshots and results:', OUT)
