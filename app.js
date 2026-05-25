// ============================================================================
// A. R. Rahman Discography — App Logic
// ============================================================================

(function () {
  'use strict';

  const DATA_PATH = './data/discography.json';
  const scriptEl = document.currentScript;

  function normalizeDiscography(data) {
    const categories = Array.isArray(data) ? data : data && data.categories;
    if (!Array.isArray(categories)) {
      throw new Error('Discography data must contain a categories array.');
    }
    return {
      categories,
      quality: data.quality || { missingLinks: [], missingSources: [] },
    };
  }

  async function loadDiscography() {
    const embedded = document.getElementById('discography-data');
    if (embedded) {
      return normalizeDiscography(JSON.parse(embedded.textContent || '{}'));
    }

    const baseUrl = scriptEl && scriptEl.src ? scriptEl.src : window.location.href;
    const response = await fetch(new URL(DATA_PATH, baseUrl));
    if (!response.ok) {
      throw new Error(`Discography data request failed with HTTP ${response.status}.`);
    }
    return normalizeDiscography(await response.json());
  }

  function showDataError(error) {
    console.error('Unable to load discography data:', error);
    const empty = document.getElementById('empty');
    if (!empty) return;
    const title = empty.querySelector('.empty-title');
    const detail = title ? title.nextElementSibling : null;
    if (title) title.textContent = 'Discography data could not load.';
    if (detail) {
      detail.textContent = window.location.protocol === 'file:'
        ? 'Serve this folder with python3 -m http.server 8000, then open http://localhost:8000.'
        : 'Refresh the page or check that data/discography.json is published.';
    }
    empty.classList.add('show');
  }

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

  const iconSpotify = `<svg viewBox="0 0 24 24" fill="currentColor"><path d="M12 0C5.4 0 0 5.4 0 12s5.4 12 12 12 12-5.4 12-12C24 5.4 18.66 0 12 0zm5.521 17.34c-.24.359-.66.48-1.021.24-2.82-1.74-6.36-2.101-10.561-1.141-.418.122-.779-.179-.899-.539-.12-.421.18-.78.54-.9 4.56-1.021 8.52-.6 11.64 1.32.42.18.479.659.301 1.02zm1.44-3.3c-.301.42-.841.6-1.262.3-3.239-1.98-8.159-2.58-11.939-1.38-.479.12-1.02-.12-1.14-.6-.12-.48.12-1.021.6-1.141C9.6 9.9 15 10.561 18.72 12.84c.361.181.54.78.241 1.2zm.12-3.36C15.24 8.4 8.82 8.16 5.16 9.301c-.6.179-1.2-.181-1.38-.721-.18-.601.18-1.2.72-1.381 4.26-1.26 11.28-1.02 15.721 1.621.539.3.719 1.02.419 1.56-.299.421-1.02.599-1.559.3z"/></svg>`;
  const iconYouTube = `<svg viewBox="0 0 24 24" fill="currentColor"><path d="M23.498 6.186a3.016 3.016 0 0 0-2.122-2.136C19.505 3.545 12 3.545 12 3.545s-7.505 0-9.377.505A3.017 3.017 0 0 0 .502 6.186C0 8.07 0 12 0 12s0 3.93.502 5.814a3.016 3.016 0 0 0 2.122 2.136c1.871.505 9.376.505 9.376.505s7.505 0 9.377-.505a3.015 3.015 0 0 0 2.122-2.136C24 15.93 24 12 24 12s0-3.93-.502-5.814zM9.545 15.568V8.432L15.818 12l-6.273 3.568z"/></svg>`;
  const iconApple = `<svg viewBox="0 0 24 24" fill="currentColor"><path d="M17.7 3.4c-.9.1-2 .7-2.7 1.5-.6.7-1.1 1.8-1 2.8 1 .1 2-.5 2.7-1.3.7-.8 1.1-1.9 1-3zM21 17.4c-.5 1.1-.8 1.6-1.5 2.6-1 1.4-2.4 3.1-4.1 3.1-1.5 0-1.9-1-3.9-1s-2.5 1-4 1c-1.7 0-3-1.6-4-3C1.2 16.8.9 10.8 2.5 8.1c1.1-1.9 2.9-3.1 4.6-3.1 1.8 0 2.9 1 4.3 1 1.4 0 2.3-1 4.4-1 1.6 0 3.3.9 4.4 2.4-3.9 2.1-3.3 7.6.8 10z"/></svg>`;
  const iconWeb = `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><path d="M2 12h20"/><path d="M12 2a15.3 15.3 0 0 1 0 20"/><path d="M12 2a15.3 15.3 0 0 0 0 20"/></svg>`;

  const providers = {
    spotify: {
      label: 'Spotify',
      className: 'spotify',
      icon: iconSpotify,
      search: (q) => 'https://open.spotify.com/search/' + encodeURIComponent('A R Rahman ' + q),
    },
    youtubeMusic: {
      label: 'YouTube Music',
      className: 'youtube',
      icon: iconYouTube,
      search: (q) => 'https://music.youtube.com/search?q=' + encodeURIComponent('A R Rahman ' + q),
    },
    youtube: {
      label: 'YouTube',
      className: 'youtube',
      icon: iconYouTube,
      search: (q) => 'https://www.youtube.com/results?search_query=' + encodeURIComponent('A R Rahman ' + q),
    },
    appleMusic: {
      label: 'Apple Music',
      className: 'apple',
      icon: iconApple,
      search: (q) => 'https://music.apple.com/search?term=' + encodeURIComponent('A R Rahman ' + q),
    },
    web: {
      label: 'Web',
      className: 'web',
      icon: iconWeb,
      search: (q) => 'https://www.google.com/search?q=' + encodeURIComponent('A R Rahman ' + q + ' official article'),
    },
  };

  const providerOrder = ['spotify', 'youtubeMusic', 'appleMusic', 'youtube'];

  function renderProviderLinks(query, links = {}, providerIds = providerOrder) {
    return providerIds.map((providerId) => {
      const provider = providers[providerId];
      if (!provider) return '';
      const directUrl = links && links[providerId];
      if (!directUrl && !provider.search) return '';
      const href = directUrl || provider.search(query);
      const mode = directUrl ? 'Open' : 'Search';
      return `<a class="provider-link ${provider.className} ${directUrl ? '' : 'generated'}" href="${escapeHtml(href)}" target="_blank" rel="noopener" title="${mode} ${provider.label}: ${escapeHtml(query)}" aria-label="${mode} ${provider.label}: ${escapeHtml(query)}">
        ${provider.icon}
      </a>`;
    }).join('');
  }

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

  function legacyVersions(film) {
    return ['t','te','h','m','o'].reduce((versions, key) => {
      if (!film[key]) return versions;
      const parts = film[key].split('•');
      versions.push({
        language: langLabels[key],
        title: (parts[0] || film[key]).trim(),
        date: (parts[1] || '').trim(),
      });
      return versions;
    }, []);
  }

  function filmProviderQuery(title, language) {
    const usefulLanguage = language && language !== 'Other' && language !== 'Version' ? language : '';
    return [title, usefulLanguage].filter(Boolean).join(' ');
  }

  function renderFilmEntry(film, idx, subsectionProviders) {
    const versions = Array.isArray(film.versions) ? film.versions : legacyVersions(film);
    if (!versions.length) return '';

    const primaryVersion = versions[0];
    const primaryTitle = primaryVersion.title || '';

    // searchable text (used for filter)
    const searchText = (
      versions.map(v => [v.language, v.title, v.date].join(' ')).join(' ') + ' ' + (film.note || '') + ' ' + (film.year || film.y || '')
    ).toLowerCase();

    const yearStr = film.year || film.y || '';
    const noteHtml = film.note ? `<div class="entry-note">${highlight(film.note)}</div>` : '';

    const versionsHtml = versions.map((version, versionIndex) => {
      const title = version.title || '';
      const date = version.date || '';
      return `<div class="entry-version">
        <span class="lang ${versionIndex === 0 ? 'primary' : ''}">${escapeHtml(version.language || 'Version')}</span>
        <span class="version-title">${highlight(title)}</span>
        ${date ? `<span class="version-date">${highlight(date)}</span>` : ''}
        <span class="version-actions">${renderProviderLinks(filmProviderQuery(title, version.language), version.links, version.providers || film.providers || subsectionProviders)}</span>
      </div>`;
    }).join('');

    return `<div class="entry" data-search="${escapeHtml(searchText)}">
      <div class="entry-top">
        <div class="entry-title">${highlight(primaryTitle)}</div>
        <div class="entry-year">${yearStr}</div>
      </div>
      <div class="entry-versions">
        ${versionsHtml}
      </div>
      ${noteHtml}
    </div>`;
  }

  // ---------- Render compact list items (everything except films) ----------
  function renderListItem(item, subsectionProviders) {
    const title = item.title || '';
    const date = item.date || '';
    const year = item.year || item.y || '';
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
        ${renderProviderLinks(q, item.links, item.providers || subsectionProviders)}
      </div>
    </div>`;
  }

  // ---------- Render whole sections ----------
  function renderSubsection(sub) {
    if (!sub.items || sub.items.length === 0) return '';
    let entriesHtml = '';
    if (sub.type === 'films') {
      entriesHtml = sub.items.map(item => renderFilmEntry(item, null, sub.providers)).join('');
    } else {
      entriesHtml = sub.items.map(item => renderListItem(item, sub.providers)).join('');
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

  function providerIcons(providerIds) {
    return providerIds.map((providerId) => {
      const provider = providers[providerId];
      if (!provider) return '';
      return `<span class="missing-provider ${provider.className}" title="${provider.label}" aria-label="${provider.label}">${provider.icon}</span>`;
    }).join('');
  }

  function renderQualityItem(item, kind) {
    const label = item.label || 'Untitled';
    const language = item.language ? ` · ${item.language}` : '';
    const year = item.year || '—';
    const context = [item.category, item.subsection].filter(Boolean).join(' / ');
    const missing = kind === 'links'
      ? `<div class="missing-list">${providerIcons(item.missing || [])}</div>`
      : '<div class="missing-list source-missing">Source citation</div>';
    const searchText = [label, language, year, context, (item.missing || []).join(' '), kind].join(' ').toLowerCase();
    return `<div class="entry quality-entry" data-search="${escapeHtml(searchText)}">
      <div class="entry-top">
        <div class="entry-title">${highlight(label)}${language ? `<em>${highlight(language)}</em>` : ''}</div>
        <div class="entry-year">${year}</div>
      </div>
      <div class="entry-note">${escapeHtml(context)}</div>
      ${missing}
    </div>`;
  }

  function renderQualitySubsection(id, title, items, kind) {
    return `<div class="subsection" data-sub-id="${id}">
      <div class="sub-head">
        <span class="sub-num">QA</span>
        <span class="sub-title">${escapeHtml(title)}</span>
        <span class="sub-count">${items.length} entries</span>
      </div>
      <div class="grid">
        ${items.map(item => renderQualityItem(item, kind)).join('')}
      </div>
    </div>`;
  }

  function renderQualitySection(quality) {
    const missingLinks = quality.missingLinks || [];
    const missingSources = quality.missingSources || [];
    return `<section class="section data-quality hidden" id="section-data-quality" data-section-id="data-quality">
      <div class="section-head">
        <div class="section-num">QA</div>
        <h2 class="section-title">Missing Links / Sources</h2>
        <div class="section-count">${missingLinks.length + missingSources.length} gaps</div>
      </div>
      <p style="color:var(--ink-dim);font-size:14px;max-width:70ch;margin-bottom:32px;line-height:1.6;font-style:italic;">
        Direct provider links and source citations can be added in the source JSON files. Generated search links remain available in the main archive while these gaps are filled.
      </p>
      ${renderQualitySubsection('missing-links', 'Missing direct provider links', missingLinks, 'links')}
      ${renderQualitySubsection('missing-sources', 'Missing source citations', missingSources, 'sources')}
    </section>`;
  }

  // ---------- Mount ----------
  function mount(discography) {
  const sections = discography.categories;
  const quality = discography.quality || { missingLinks: [], missingSources: [] };
  const main = document.getElementById('main');
  const empty = document.getElementById('empty');
  const sectionsHtml = sections.map(renderSection).join('') + renderQualitySection(quality);
  // Insert before empty state
  main.insertAdjacentHTML('afterbegin', sectionsHtml);

  // ---------- Build category nav ----------
  const catsContainer = document.getElementById('cats');
  const stickyBar = document.querySelector('.search-bar');
  const cats = [{ id: 'all', label: 'All' }]
    .concat(sections.map(s => ({ id: s.id, label: s.title })))
    .concat([{ id: 'data-quality', label: 'Missing Links / Sources' }]);
  catsContainer.innerHTML = cats.map((c, i) =>
    `<button class="cat-pill ${i === 0 ? 'active' : ''}" type="button" data-cat="${c.id}" aria-pressed="${i === 0 ? 'true' : 'false'}">${escapeHtml(c.label)}</button>`
  ).join('');

  function setActiveCategoryButton(categoryId) {
    document.querySelectorAll('.cat-pill').forEach(pill => {
      const isActive = pill.getAttribute('data-cat') === categoryId;
      pill.classList.toggle('active', isActive);
      pill.setAttribute('aria-pressed', isActive ? 'true' : 'false');
    });
  }

  // ---------- Stats ----------
  const countSectionEntries = (section) =>
    (section.subsections || []).reduce((count, subsection) => count + (subsection.items ? subsection.items.length : 0), 0);

  const splitStatIds = (value) =>
    (value || '').split(',').map(id => id.trim()).filter(Boolean);

  function computeStats() {
    const categoryCounts = new Map();
    const subsectionCounts = new Map();
    let total = 0;

    sections.forEach(section => {
      const sectionTotal = countSectionEntries(section);
      categoryCounts.set(section.id, sectionTotal);
      total += sectionTotal;
      (section.subsections || []).forEach(subsection => {
        subsectionCounts.set(subsection.id, subsection.items ? subsection.items.length : 0);
      });
    });

    document.querySelectorAll('.stat-num').forEach(statEl => {
      if (statEl.dataset.statTotal === 'true') {
        statEl.textContent = total;
        return;
      }

      const categoryTotal = splitStatIds(statEl.dataset.statCategories)
        .reduce((sum, id) => sum + (categoryCounts.get(id) || 0), 0);
      const subsectionTotal = splitStatIds(statEl.dataset.statSubsections)
        .reduce((sum, id) => sum + (subsectionCounts.get(id) || 0), 0);
      statEl.textContent = categoryTotal + subsectionTotal;
    });

    document.getElementById('match-count').textContent = total;
  }
  computeStats();

  // ---------- Filter / Search ----------
  const searchInput = document.getElementById('search');
  const clearBtn = document.getElementById('clear');
  const countEl = document.getElementById('match-count');
  const resultNav = document.getElementById('result-nav');
  const resultPrev = document.getElementById('result-prev');
  const resultNext = document.getElementById('result-next');
  const resultPosition = document.getElementById('result-position');
  let activeCat = 'all';
  let activeResultIndex = -1;
  let visibleResults = [];

  // Cache entries and subsections for fast filtering
  const allEntries = Array.from(document.querySelectorAll('.entry'));
  const allSubsections = Array.from(document.querySelectorAll('.subsection'));
  const allSections = Array.from(document.querySelectorAll('.section'));

  function syncResultNav() {
    const hasScopedResults = visibleResults.length > 0 && (currentQuery || activeCat !== 'all');
    resultNav.hidden = !hasScopedResults;
    resultPrev.disabled = !hasScopedResults || visibleResults.length <= 1;
    resultNext.disabled = !hasScopedResults || visibleResults.length <= 1;
    resultPosition.textContent = hasScopedResults && activeResultIndex >= 0
      ? `${activeResultIndex + 1} / ${visibleResults.length}`
      : '—';
  }

  function setActiveResult(index, shouldScroll) {
    allEntries.forEach(el => el.classList.remove('active-result'));

    if (index < 0 || visibleResults.length === 0) {
      activeResultIndex = -1;
      syncResultNav();
      return;
    }

    activeResultIndex = ((index % visibleResults.length) + visibleResults.length) % visibleResults.length;
    const activeResult = visibleResults[activeResultIndex];
    activeResult.classList.add('active-result');
    syncResultNav();

    if (shouldScroll) {
      activeResult.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }
  }

  function navigateResults(delta) {
    if (visibleResults.length === 0 || resultNav.hidden) return;
    const nextIndex = activeResultIndex < 0 ? 0 : activeResultIndex + delta;
    setActiveResult(nextIndex, true);
  }

  function applyFilter(options = {}) {
    const previousActive = activeResultIndex >= 0 ? visibleResults[activeResultIndex] : null;
    const query = searchInput.value.trim().toLowerCase();
    const previousQuery = currentQuery;
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
      const catMatch = sid === 'data-quality'
        ? activeCat === sid
        : (activeCat === 'all' || activeCat === sid);
      const hasVisible = sec.querySelectorAll('.subsection:not(.hidden)').length > 0;
      sec.classList.toggle('hidden', !catMatch || !hasVisible);
    });

    // Recount only entries in visible sections.
    visibleCount = 0;
    allSections.forEach(sec => {
      if (sec.classList.contains('hidden')) return;
      visibleCount += sec.querySelectorAll('.entry:not(.hidden)').length;
    });

    countEl.textContent = visibleCount;
    clearBtn.hidden = (!query && activeCat === 'all');
    visibleResults = allEntries.filter(el => {
      if (el.classList.contains('hidden')) return false;
      const section = el.closest('.section');
      return section && !section.classList.contains('hidden');
    });

    if (visibleResults.length > 0 && (query || activeCat !== 'all')) {
      const retainedIndex = previousActive ? visibleResults.indexOf(previousActive) : -1;
      const nextIndex = retainedIndex >= 0 ? retainedIndex : 0;
      setActiveResult(nextIndex, Boolean(options.scrollToFirst && query && query !== previousQuery));
    } else {
      setActiveResult(-1, false);
    }

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
    const selectors = '.entry:not(.hidden) .entry-title, .entry:not(.hidden) .entry-note, .entry:not(.hidden) .version-title, .entry:not(.hidden) .version-date, .entry:not(.hidden) .missing-list';
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
    searchTimer = setTimeout(() => applyFilter({ scrollToFirst: true }), 100);
  });

  clearBtn.addEventListener('click', () => {
    searchInput.value = '';
    activeCat = 'all';
    setActiveCategoryButton(activeCat);
    applyFilter();
    searchInput.focus();
  });

  catsContainer.addEventListener('click', (e) => {
    const btn = e.target.closest('.cat-pill');
    if (!btn) return;
    const cat = btn.getAttribute('data-cat');
    activeCat = cat;
    setActiveCategoryButton(activeCat);
    applyFilter();
    // Scroll to section
    if (cat !== 'all') {
      const target = document.getElementById('section-' + cat);
      if (target) {
        const stickyOffset = stickyBar ? stickyBar.offsetHeight + 24 : 120;
        const top = target.getBoundingClientRect().top + window.pageYOffset - stickyOffset;
        window.scrollTo({ top, behavior: 'smooth' });
      }
    } else {
      window.scrollTo({ top: 0, behavior: 'smooth' });
    }
  });

  resultPrev.addEventListener('click', () => navigateResults(-1));
  resultNext.addEventListener('click', () => navigateResults(1));

  // Initial filter pass (no query)
  applyFilter();

  // Keyboard shortcut: / to focus search
  document.addEventListener('keydown', (e) => {
    if (e.key === '/' && document.activeElement !== searchInput) {
      e.preventDefault();
      searchInput.focus();
    }
    if (e.key === 'Enter' && document.activeElement === searchInput && !resultNav.hidden) {
      e.preventDefault();
      navigateResults(e.shiftKey ? -1 : 1);
    }
    if (e.key === 'Escape' && document.activeElement === searchInput) {
      searchInput.value = '';
      applyFilter();
    }
  });
  }

  async function start() {
    try {
      mount(await loadDiscography());
    } catch (error) {
      showDataError(error);
    }
  }

  start();
})();
