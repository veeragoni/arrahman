# A. R. Rahman — Complete Discography

A searchable, beautifully-typeset web archive of every film score, dub, single, album, advertisement, stage musical, documentary, collaboration, and book associated with the composer.

> Compiled from the discography database curated by Gopal Srinivasan, Mohan Bhagavathi, and Dinesh Vaidya. Film table edition: 27 January 2026. Non-film edition: 15 May 2026.

**[Live demo →](./dist/arrahman-discography.html)** (or open `index.html` directly in any browser)

---

## What's in here

```
.
├── index.html              # main page — open this locally or deploy to a host
├── app.js                  # search, filter, render logic
├── data/                   # ← edit these files to add or change entries
│   ├── 01-films.js         # film compositions (Tamil/Telugu/Hindi/Malayalam/Other)
│   ├── 02-nonfilm.js       # albums, singles, TV/web series, stage musicals, etc.
│   ├── 03-ads.js           # advertisements and ringtones
│   ├── 04-other.js         # labels, foundations, music supervision, books, etc.
│   ├── 05-videos.js        # on-camera music release performances
│   └── index.js            # section manifest (only edit if adding a new top-level category)
├── scripts/
│   └── build.py            # bundles everything into a single HTML file (optional)
└── dist/
    └── arrahman-discography.html   # single-file build output
```

Total: **739 entries** across 5 categories. No external dependencies (Google Fonts loaded from CDN).

---

## How to add or edit entries

Every entry lives in one of the files in `data/`. The format is plain JavaScript — no JSON commas to fight, comments are allowed, trailing commas are fine.

### 1. To add a film (`data/01-films.js`)

Films are stored as rows where each language column is its own field. Use only the fields you need:

```js
{ y: 2025, t: "Some Tamil Title • 15-08-2025", h: "Hindi Dub Title • 22-08-2025" },
```

| Field  | Meaning                          | Example                       |
|--------|----------------------------------|-------------------------------|
| `y`    | Primary year (number, required)  | `2025`                        |
| `t`    | Tamil release                    | `"Title • 15-08-2025"`        |
| `te`   | Telugu release                   | `"Title • 2025"`              |
| `h`    | Hindi release                    | `"Title • DD-MM-YYYY"`        |
| `m`    | Malayalam release                | `"Title • DD-MM-YYYY"`        |
| `o`    | Other language (Kannada, Marathi, English, etc.) | `"Title (Marathi) • 2026"` |
| `note` | Free-text note shown in italics  | `"Score only"`                |

The format inside each language field is `"<Title> • <Date>"`. Date can be either `DD-MM-YYYY` or just `YYYY`. The site renders it nicely either way.

**Tamil-undubbed, Telugu-undubbed, Hindi-undubbed, etc.** have their own arrays at the bottom of `01-films.js` — same structure as the non-film entries below.

### 2. To add a non-film entry (most other files)

Singles, albums, TV series, ads, books, theme songs — they all use the same shape:

```js
{ title: "Song or Album Name", year: 2025, date: "15-08-2025", note: "Optional note" },
```

Only `title` is required. Find the right array (e.g. `SINGLES`, `ADS_POST_2000`, `BOOKS_SELF`) and append your entry.

### 3. To add a brand-new category

Open `data/index.js`. The `SECTIONS` array drives the entire UI. Add a new subsection inside an existing section, or define a whole new section:

```js
{
  id: 'my-new-category',
  num: '6.10',
  title: 'My New Category',
  type: 'list',
  items: MY_NEW_ARRAY,  // defined in one of the data files
},
```

Then declare `MY_NEW_ARRAY` in any data file. The page will pick it up automatically.

### 4. To preview your changes

Just open `index.html` in a browser. **No build step required.** If you have Python installed, you can also serve it locally to avoid `file://` quirks:

```bash
python3 -m http.server 8000
# then visit http://localhost:8000
```

### 5. (Optional) To build a single-file version

If you want one self-contained HTML file you can email, attach, or upload anywhere:

```bash
python3 scripts/build.py
# → dist/arrahman-discography.html
```

This produces a single ~90 KB HTML file with everything inlined.

---

## Deploy to GitHub Pages

1. Push to GitHub (see commands below).
2. In your repo on github.com → **Settings → Pages**.
3. Source: **Deploy from a branch**, branch: `main`, folder: `/ (root)`.
4. Wait ~30 seconds. Your site will be live at `https://<username>.github.io/<reponame>/`.

That's it — no build pipeline required because everything is static.

---

## Initial git push

From your machine, in this directory:

```bash
git init
git add .
git commit -m "Initial commit: A. R. Rahman discography site"
git branch -M main

# Replace with your repo URL:
git remote add origin https://github.com/<your-username>/arrahman-discography.git
git push -u origin main
```

If you don't have the repo yet:

```bash
# Using GitHub CLI:
gh repo create arrahman-discography --public --source=. --remote=origin --push

# Or manually create it on github.com first, then run the `git remote add` + `git push` above.
```

---

## How search works

- The top search bar filters every entry in real time. Matches are highlighted in amber.
- The category pills below the search filter to a single section.
- Press `/` from anywhere to focus the search box. Press `Esc` to clear.
- Each entry links to Spotify and YouTube Music searches for that title (`A R Rahman <title>`), so clicks lead to real results — no fabricated album IDs.

---

## Design

The site uses **Fraunces** (variable serif) for display type and **Manrope** for body text, with **JetBrains Mono** for dates. The palette is a warm dark theme: deep midnight (`#0f1014`), cream ink (`#ecead7`), and a saffron-gold accent (`#d4a574`) that nods to Indian classical tradition.

CSS lives inside `<style>` in `index.html`. All design tokens are CSS custom properties at the top — change one variable, the whole site updates.

---

## License & credits

Data compiled by Gopal Srinivasan, Mohan Bhagavathi, and Dinesh Vaidya from the source PDFs. This site is a fan archive and is not affiliated with A. R. Rahman or any of his labels.

Spotify links use Spotify's public search URL pattern; YouTube Music links use YouTube Music's public search URL pattern. No private API keys or affiliations.
