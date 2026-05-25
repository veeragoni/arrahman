// ============================================================================
// A. R. Rahman Discography — App Logic
// ============================================================================

(function () {
  'use strict';

  const sections = window.SECTIONS;

  // ---------- Helpers ----------
  const escapeHtml = (str) => {
    if (str == null) return '';
    return String(str)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#39;');
  };

  // Spotify and YouTube Music search URLs — these are real search endpoints,
  // so we're not fabricating album IDs. They'll show real results for the query.
  const spotifySearch = (q) =>
    'https://open.spotify.com/search/' + encodeURIComponent('A R Rahman ' + q);
  const youtubeSearch = (q) =>
    'https://music.youtube.com/search?q=' + encodeURIComponent('A R Rahman ' + q);

  const iconSpotify = `<svg viewBox="0 0 24 24" fill="currentColor"><path d="M12 0C5.4 0 0 5.4 0 12s5.4 12 12 12 12-5.4 12-12C24 5.4 18.66 0 12 0zm5.521 17.34c-.24.359-.66.48-1.021.24-2.82-1.74-6.36-2.101-10.561-1.141-.418.122-.779-.179-.899-.539-.12-.421.18-.78.54-.9 4.56-1.021 8.52-.6 11.64 1.32.42.18.479.659.301 1.02zm1.44-3.3c-.301.42-.841.6-1.262.3-3.239-1.98-8.159-2.58-11.939-1.38-.479.12-1.02-.12-1.14-.6-.12-.48.12-1.021.6-1.141C9.6 9.9 15 10.561 18.72 12.84c.361.181.54.78.241 1.2zm.12-3.36C15.24 8.4 8.82 8.16 5.16 9.301c-.6.179-1.2-.181-1.38-.721-.18-.601.18-1.2.72-1.381 4.26-1.26 11.28-1.02 15.721 1.621.539.3.719 1.02.419 1.56-.299.421-1.02.599-1.559.3z"/></svg>`;
  const iconYouTube = `<svg viewBox="0 0 24 24" fill="currentColor"><path d="M23.498 6.186a3.016 3.016 0 0 0-2.122-2.136C19.505 3.545 12 3.545 12 3.545s-7.505 0-9.377.505A3.017 3.017 0 0 0 .502 6.186C0 8.07 0 12 0 12s0 3.93.502 5.814a3.016 3.016 0 0 0 2.122 2.136c1.871.505 9.376.505 9.376.505s7.505 0 9.377-.505a3.015 3.015 0 0 0 2.122-2.136C24 15.93 24 12 24 12s0-3.93-.502-5.814zM9.545 15.568V8.432L15.818 12l-6.273 3.568z"/></svg>`;

  // ---------- Highlight matches ----------
  let currentQuery = '';
  const highlight = (text) => {
    if (!currentQuery) return escapeHtml(text);
    const esc = escapeHtml(text);
    try {
      const re = new RegExp('(' + currentQuery.replace(/[.*+?^${}()|[\]\\]/g, '\\$&') + ')', 'gi');
      return esc.replace(re, '<mark>$1</mark>');
    } catch (e) {
      return esc;
    }
  };

  // ---------- Render film entries (multi-language) ----------
  const langLabels = { t: 'Tamil', te: 'Telugu', h: 'Hindi', m: 'Malayalam', o: 'Other' };

  function renderFilmEntry(film, idx) {
    // pick primary title (prefer Tamil > Telugu > Hindi > Malayalam > Other)
    const primaryField = ['t','te','h','m','o'].find(k => film[k]);
    if (!primaryField) return '';
    const primaryFull = film[primaryField];

    // primary title is the part before "•"
    const primaryTitle = (primaryFull.split('•')[0] || primaryFull).trim();

    // collect all language versions
    const versions = [];
    ['t','te','h','m','o'].forEach(k => {
      if (film[k]) versions.push({ lang: langLabels[k], text: film[k], primary: k === primaryField });
    });

    // searchable text (used for filter)
    const searchText = (
      versions.map(v => v.text).join(' ') + ' ' + (film.note || '') + ' ' + film.y
    ).toLowerCase();

    const yearStr = film.y || '';
    const noteHtml = film.note ? `<div class="entry-note">${highlight(film.note)}</div>` : '';

    const langsHtml = versions.map(v => {
      const titlePart = v.text.split('•')[0].trim();
      const datePart = (v.text.split('•')[1] || '').trim();
      return `<div class="entry-langs">
        <span class="lang ${v.primary ? 'primary' : ''}">${v.lang}</span>
        <span style="font-size:12px;color:var(--ink-dim);">${highlight(titlePart)}</span>
        ${datePart ? `<span style="font-family:var(--mono);font-size:10px;color:var(--ink-faint);margin-left:auto;">${highlight(datePart)}</span>` : ''}
      </div>`;
    }).join('');

    const q = primaryTitle;
    return `<div class="entry" data-search="${escapeHtml(searchText)}">
      <div class="entry-top">
        <div class="entry-title">${highlight(primaryTitle)}</div>
        <div class="entry-year">${yearStr}</div>
      </div>
      <div style="display:flex;flex-direction:column;gap:4px;margin-top:4px;">
        ${langsHtml}
      </div>
      ${noteHtml}
      <div class="entry-actions">
        <a class="action-link spotify" href="${spotifySearch(q)}" target="_blank" rel="noopener">
          ${iconSpotify} Spotify
        </a>
        <a class="action-link youtube" href="${youtubeSearch(q)}" target="_blank" rel="noopener">
          ${iconYouTube} YouTube Music
        </a>
      </div>
    </div>`;
  }

  // ---------- Render compact list items (everything except films) ----------
  function renderListItem(item) {
    const title = item.title || '';
    const date = item.date || '';
    const year = item.year || '';
    const note = item.note || '';
    const meta = date || year || '—';
    const searchText = (title + ' ' + date + ' ' + year + ' ' + note).toLowerCase();
    const noteHtml = note ? ` <em style="color:var(--ink-faint);font-style:italic;">· ${highlight(note)}</em>` : '';
    const q = title;
    return `<div class="entry" data-search="${escapeHtml(searchText)}">
      <div class="entry-top">
        <div class="entry-title">${highlight(title)}${noteHtml}</div>
        <div class="entry-year">${meta}</div>
      </div>
      <div class="entry-actions">
        <a class="action-link spotify" href="${spotifySearch(q)}" target="_blank" rel="noopener">
          ${iconSpotify} Spotify
        </a>
        <a class="action-link youtube" href="${youtubeSearch(q)}" target="_blank" rel="noopener">
          ${iconYouTube} YouTube Music
        </a>
      </div>
    </div>`;
  }

  // ---------- Render whole sections ----------
  function renderSubsection(sub) {
    if (!sub.items || sub.items.length === 0) return '';
    let entriesHtml = '';
    if (sub.type === 'films') {
      entriesHtml = sub.items.map(renderFilmEntry).join('');
    } else {
      entriesHtml = sub.items.map(renderListItem).join('');
    }
    return `<div class="subsection" data-sub-id="${sub.id}">
      <div class="sub-head">
        <span class="sub-num">${sub.num}</span>
        <span class="sub-title">${escapeHtml(sub.title)}</span>
        <span class="sub-count">${sub.items.length} entries</span>
      </div>
      <div class="grid">
        ${entriesHtml}
      </div>
    </div>`;
  }

  function renderSection(section) {
    // count
    let total = 0;
    section.subsections.forEach(s => total += (s.items ? s.items.length : 0));
    const subsHtml = section.subsections.map(renderSubsection).join('');
    return `<section class="section" id="section-${section.id}" data-section-id="${section.id}">
      <div class="section-head">
        <div class="section-num">${section.num}</div>
        <h2 class="section-title">${escapeHtml(section.title)}</h2>
        <div class="section-count">${total} entries</div>
      </div>
      ${section.blurb ? `<p style="color:var(--ink-dim);font-size:14px;max-width:60ch;margin-bottom:32px;line-height:1.6;font-style:italic;">${escapeHtml(section.blurb)}</p>` : ''}
      ${subsHtml}
    </section>`;
  }

  // ---------- Mount ----------
  const main = document.getElementById('main');
  const empty = document.getElementById('empty');
  const sectionsHtml = sections.map(renderSection).join('');
  // Insert before empty state
  main.insertAdjacentHTML('afterbegin', sectionsHtml);

  // ---------- Build category nav ----------
  const catsContainer = document.getElementById('cats');
  const cats = [{ id: 'all', label: 'All' }].concat(
    sections.map(s => ({ id: s.id, label: s.title }))
  );
  catsContainer.innerHTML = cats.map((c, i) =>
    `<button class="cat-pill ${i === 0 ? 'active' : ''}" data-cat="${c.id}">${escapeHtml(c.label)}</button>`
  ).join('');

  // ---------- Stats ----------
  function computeStats() {
    const films = (sections.find(s => s.id === 'films')?.subsections || [])
      .reduce((a, s) => a + s.items.length, 0);
    const singles = (sections.find(s => s.id === 'nonfilm')?.subsections || [])
      .reduce((a, s) => a + s.items.length, 0);
    const ads = (sections.find(s => s.id === 'ads')?.subsections || [])
      .reduce((a, s) => a + s.items.length, 0);
    const total = sections.reduce((a, sec) =>
      a + sec.subsections.reduce((b, s) => b + s.items.length, 0), 0);
    document.getElementById('stat-films').textContent = films;
    document.getElementById('stat-singles').textContent = singles;
    document.getElementById('stat-ads').textContent = ads;
    document.getElementById('stat-total').textContent = total;
    document.getElementById('match-count').textContent = total;
  }
  computeStats();

  // ---------- Filter / Search ----------
  const searchInput = document.getElementById('search');
  const clearBtn = document.getElementById('clear');
  const countEl = document.getElementById('match-count');
  let activeCat = 'all';

  // Cache entries and subsections for fast filtering
  const allEntries = Array.from(document.querySelectorAll('.entry'));
  const allSubsections = Array.from(document.querySelectorAll('.subsection'));
  const allSections = Array.from(document.querySelectorAll('.section'));

  function applyFilter() {
    const query = searchInput.value.trim().toLowerCase();
    currentQuery = query;
    let visibleCount = 0;

    // First pass: entries
    allEntries.forEach(el => {
      const text = el.getAttribute('data-search') || '';
      const matchesQuery = !query || text.indexOf(query) !== -1;
      if (matchesQuery) {
        el.classList.remove('hidden');
        visibleCount++;
      } else {
        el.classList.add('hidden');
      }
    });

    // Hide subsections with no visible entries
    allSubsections.forEach(sub => {
      const visibleEntries = sub.querySelectorAll('.entry:not(.hidden)').length;
      sub.classList.toggle('hidden', visibleEntries === 0);
    });

    // Filter by category and hide sections with no visible content
    allSections.forEach(sec => {
      const sid = sec.getAttribute('data-section-id');
      const catMatch = (activeCat === 'all' || activeCat === sid);
      const hasVisible = sec.querySelectorAll('.subsection:not(.hidden)').length > 0;
      sec.classList.toggle('hidden', !catMatch || !hasVisible);
    });

    // Recount only entries within visible sections+category
    if (activeCat !== 'all' || query) {
      let recount = 0;
      allSections.forEach(sec => {
        if (sec.classList.contains('hidden')) return;
        recount += sec.querySelectorAll('.entry:not(.hidden)').length;
      });
      visibleCount = recount;
    }

    countEl.textContent = visibleCount;
    clearBtn.hidden = (!query && activeCat === 'all');

    // empty state
    const allHidden = !Array.from(document.querySelectorAll('.section')).some(s => !s.classList.contains('hidden'));
    empty.classList.toggle('show', allHidden && (query || activeCat !== 'all'));

    // re-highlight: requires re-render of visible matches. For perf, only highlight on query change.
    if (query) {
      reHighlight(query);
    } else {
      removeHighlights();
    }
  }

  // Highlight: walk through visible entries' relevant text nodes and wrap matches in <mark>
  function reHighlight(query) {
    removeHighlights();
    if (!query) return;
    const escaped = query.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
    const re = new RegExp('(' + escaped + ')', 'gi');
    const selectors = '.entry:not(.hidden) .entry-title, .entry:not(.hidden) .entry-note, .entry:not(.hidden) .entry-langs span';
    document.querySelectorAll(selectors).forEach(el => {
      // skip if already highlighted
      if (el.querySelector('mark')) return;
      const html = el.innerHTML;
      // Only highlight text not inside tags. Simple approach: split on tags.
      const parts = html.split(/(<[^>]+>)/g);
      const newHtml = parts.map(p => {
        if (p.startsWith('<')) return p;
        return p.replace(re, '<mark>$1</mark>');
      }).join('');
      el.innerHTML = newHtml;
    });
  }

  function removeHighlights() {
    document.querySelectorAll('mark').forEach(m => {
      const parent = m.parentNode;
      if (!parent) return;
      while (m.firstChild) parent.insertBefore(m.firstChild, m);
      parent.removeChild(m);
      parent.normalize();
    });
  }

  // Debounce search
  let searchTimer = null;
  searchInput.addEventListener('input', () => {
    if (searchTimer) clearTimeout(searchTimer);
    searchTimer = setTimeout(applyFilter, 100);
  });

  clearBtn.addEventListener('click', () => {
    searchInput.value = '';
    activeCat = 'all';
    document.querySelectorAll('.cat-pill').forEach(p =>
      p.classList.toggle('active', p.getAttribute('data-cat') === 'all'));
    applyFilter();
    searchInput.focus();
  });

  catsContainer.addEventListener('click', (e) => {
    const btn = e.target.closest('.cat-pill');
    if (!btn) return;
    const cat = btn.getAttribute('data-cat');
    activeCat = cat;
    document.querySelectorAll('.cat-pill').forEach(p => p.classList.remove('active'));
    btn.classList.add('active');
    applyFilter();
    // Scroll to section
    if (cat !== 'all') {
      const target = document.getElementById('section-' + cat);
      if (target) {
        const top = target.getBoundingClientRect().top + window.pageYOffset - 100;
        window.scrollTo({ top, behavior: 'smooth' });
      }
    } else {
      window.scrollTo({ top: 0, behavior: 'smooth' });
    }
  });

  // Initial filter pass (no query)
  applyFilter();

  // Keyboard shortcut: / to focus search
  document.addEventListener('keydown', (e) => {
    if (e.key === '/' && document.activeElement !== searchInput) {
      e.preventDefault();
      searchInput.focus();
    }
    if (e.key === 'Escape' && document.activeElement === searchInput) {
      searchInput.value = '';
      applyFilter();
    }
  });
})();
