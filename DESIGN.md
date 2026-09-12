# Design

## Theme

Dark, terminal-native. Not "dark mode": the page imitates a server directory listing viewed in a terminal, so dark is structural. Single theme, no toggle.

## Color

Gruvbox-derived palette, used as-is:

- Background: `#282828`
- Foreground: `#ebdbb2`
- Muted / secondary text: `#a89984` (5.30:1 against the background)
- Border/rule: `#504945`
- Link: `#83a598` (blue-green), visited `#d3869b` (pink)
- Accent / hover / focus / active: `#fe8019` (orange)
- Syntax colors (proj-json blocks): key `#fabd2f`, string `#b8bb26`, punctuation `#a89984`

Strategy: restrained. Orange is the single interaction color; everything else is filesystem-neutral.

## Typography

- Single family: JetBrains Mono (self-hosted woff2, 400 + 700). Fallback Courier.
- Body 13px, line-height 1.7. h1 26px, section h2 titles 22px, h3 16px. Metadata 11–12px.
- Monospace is load-bearing: column alignment in listings is done with character padding.

## Layout

- Two-pane grid: sticky left directory listing (~28%), scrollable right content pane.
- Listings are whitespace-aligned pre-style rows (Name / Type / Updated), sortable headers with ▲▼.
- Right pane: section title, meta line, blurb, then content (iframe / image / pdf thumb / repo link).
- Collections use a split: sub-list left, focus pane right (≥1200px).

## Components

- `.proj-json`: JSON-styled project metadata block with syntax coloring and a 1px full border.
- `.pill`: inline lowercase tag, minimal.
- `.quote`: blockquote with a 1px left rule.
- `.mkdir`: fake `$ mkdir` prompt with a labeled input, limited to 40 characters. Stores folders in localStorage when available; works in memory when storage is blocked.
- `.edu`: pre-aligned fact tables (experience, education).
- `.repo-tree`: ASCII `tree`-style file listing for repo entries.
- `.server-sig`: fake Apache `<address>` signature inside the footer; also on 404.html.
- `.cover`: static ASCII portrait in `portrait.svg`, generated offline from `selfie.png`. SVG character spacing preserves face proportions. The source PNG remains the social-share image.
- Sort controls are native buttons. Collection rows are native links. PDF thumbnails link to files; inline preview is an explicit button action.

## Routing

Hash routes mirror the filesystem: `#/selected-work/polars`, `#/visual-studies`, `#/about`, `#/contact`, `#/` home. Clicking locks + navigates (history entry per section, replaceState per item); hover-peek never touches the URL.

## Motion

Currently none beyond browser defaults. Any additions: fast (≤200ms), ease-out, opacity/transform only, honor prefers-reduced-motion. Terminal energy: instant, snappy, no float or bounce.
