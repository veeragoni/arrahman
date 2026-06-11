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

  function initAnalyticsNotice() {
    const notice = document.getElementById('analytics-notice');
    const close = document.getElementById('analytics-notice-close');
    if (!notice || !close) return;

    const storageKey = 'analytics-notice-dismissed';
    let isDismissed = false;
    try {
      isDismissed = window.localStorage.getItem(storageKey) === 'true';
    } catch (error) {
      isDismissed = false;
    }

    if (isDismissed) return;
    notice.hidden = false;

    close.addEventListener('click', () => {
      notice.hidden = true;
      try {
        window.localStorage.setItem(storageKey, 'true');
      } catch (error) {
        // Storage can be blocked; the close action should still work for this page view.
      }
    });
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

  const iconSpotify = `<svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="12" r="11.4" fill="#1DB954"/><path d="M17.82 9.98c-3.13-1.86-7.58-2.03-10.58-1.12-.5.15-1.03-.13-1.18-.63s.13-1.02.63-1.18c3.45-1.05 8.45-.84 12.09 1.32.45.27.6.85.33 1.3-.27.44-.85.58-1.29.31zm-.56 3.02c-.23.38-.72.5-1.1.27-2.61-1.6-6.58-2.07-9.66-1.13-.43.13-.87-.11-1-.53-.13-.42.11-.87.53-1 3.55-1.08 7.94-.56 10.96 1.29.38.23.5.72.27 1.1zm-1.31 2.83c-.18.3-.57.39-.87.21-2.28-1.39-5.16-1.7-8.55-.93-.34.08-.68-.13-.76-.47-.08-.34.13-.68.47-.76 3.73-.85 6.92-.49 9.51 1.09.3.18.39.57.2.86z" fill="#000000"/></svg>`;
  const iconYouTube = `<svg viewBox="0 0 24 24" aria-hidden="true"><rect x="1.5" y="5" width="21" height="14" rx="3.2" fill="#FF0000"/><path d="M10 8.65v6.7L15.8 12z" fill="#FFFFFF"/></svg>`;
  const iconYouTubeMusic = `<svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="12" r="11.4" fill="#ff0033"/><circle cx="12" cy="12" r="8.1" fill="#ff1744"/><circle cx="12" cy="12" r="5.45" fill="none" stroke="#ffffff" stroke-width="1.4"/><path d="M10.2 8.85v6.3L15.65 12z" fill="#ffffff"/></svg>`;
  const iconAppleMusic = `<svg viewBox="0 0 24 24" aria-hidden="true"><rect x="1" y="1" width="22" height="22" rx="5" fill="#fa2d55"/><path d="M16.8 5.1v9.8c0 1.55-1.31 2.72-3.02 2.72-1.43 0-2.48-.82-2.48-1.96 0-1.19 1.08-2.05 2.55-2.05.54 0 1.02.12 1.39.33V8.72l-5.35 1.05v6.13c0 1.55-1.31 2.72-3.02 2.72-1.43 0-2.48-.82-2.48-1.96 0-1.19 1.08-2.05 2.55-2.05.54 0 1.02.12 1.39.33V7.95l8.47-1.68z" fill="#ffffff"/></svg>`;
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
      className: 'ytmusic',
      icon: iconYouTubeMusic,
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
      icon: iconAppleMusic,
      search: (q) => 'https://music.apple.com/us/search?term=' + encodeURIComponent('A R Rahman ' + q),
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

  function languageKey(language) {
    const value = (language || 'Version').toString().trim().toLowerCase();
    if (!value) return 'version';
    if (value.includes('tamil')) return 'tamil';
    if (value.includes('telugu')) return 'telugu';
    if (value.includes('hindi')) return 'hindi';
    if (value.includes('malayalam')) return 'malayalam';
    if (value.includes('kannada')) return 'kannada';
    if (value.includes('other')) return 'other';
    return value.replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '') || 'version';
  }

  function languageLabel(key) {
    const labels = {
      tamil: 'Tamil',
      telugu: 'Telugu',
      hindi: 'Hindi',
      malayalam: 'Malayalam',
      kannada: 'Kannada',
      other: 'Other',
      version: 'Version',
    };
    return labels[key] || key.split('-').map(part => part.charAt(0).toUpperCase() + part.slice(1)).join(' ');
  }

  function langClass(language) {
    return 'lang-' + languageKey(language);
  }

  function collectLanguages(sections) {
    const labels = new Map();
    sections.forEach(section => {
      (section.subsections || []).forEach(subsection => {
        (subsection.items || []).forEach(item => {
          if (item.type !== 'film' && subsection.type !== 'films') return;
          const versions = Array.isArray(item.versions) ? item.versions : legacyVersions(item);
          versions.forEach(version => {
            const key = languageKey(version.language || 'Version');
            if (!labels.has(key)) labels.set(key, languageLabel(key));
          });
        });
      });
    });

    const priority = ['tamil', 'telugu', 'hindi', 'malayalam', 'kannada', 'other', 'version'];
    const priorityLanguages = priority
      .filter(key => labels.has(key))
      .map(key => ({ id: key, label: labels.get(key) }));
    const remainingLanguages = Array.from(labels.entries())
      .filter(([key]) => !priority.includes(key))
      .map(([id, label]) => ({ id, label }));
    return priorityLanguages.concat(remainingLanguages);
  }

  function releaseYear(date, fallback) {
    const match = /(19|20)\d{2}/.exec((date || '').toString());
    if (match) return match[0];
    return (fallback || '').toString().trim();
  }

  function collectYears(sections) {
    const years = new Set();
    sections.forEach(section => {
      (section.subsections || []).forEach(subsection => {
        (subsection.items || []).forEach(item => {
          if (item.type === 'film' || subsection.type === 'films') {
            const versions = Array.isArray(item.versions) ? item.versions : legacyVersions(item);
            versions.forEach(version => {
              const year = releaseYear(version.date, item.year || item.y);
              if (year) years.add(year);
            });
          } else {
            const year = releaseYear(item.date, item.year || item.y);
            if (year) years.add(year);
          }
        });
      });
    });
    return Array.from(years).sort().reverse();
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
    const languageKeys = versions.map(version => languageKey(version.language || 'Version'));
    const uniqueLanguageKeys = Array.from(new Set(languageKeys));

    // searchable text (used for filter)
    const searchText = (
      versions.map(v => [v.language, v.title, v.date].join(' ')).join(' ') + ' ' + (film.note || '') + ' ' + (film.year || film.y || '')
    ).toLowerCase();
    const entryMeta = ((film.note || '') + ' ' + (film.year || film.y || '')).toLowerCase();

    const yearStr = film.year || film.y || '';
    const noteHtml = film.note ? `<div class="entry-note">${highlight(film.note)}</div>` : '';

    const versionsHtml = versions.map((version) => {
      const title = version.title || '';
      const date = version.date || '';
      const versionLanguage = version.language || 'Version';
      const versionSearch = [versionLanguage, title, date].join(' ').toLowerCase();
      const versionYear = releaseYear(date, film.year || film.y);
      return `<div class="entry-version" data-language="${escapeHtml(languageKey(versionLanguage))}" data-year="${escapeHtml(versionYear)}" data-search="${escapeHtml(versionSearch)}">
        <span class="lang ${escapeHtml(langClass(versionLanguage))}">${escapeHtml(versionLanguage)}</span>
        <span class="version-title">${highlight(title)}</span>
        ${date ? `<span class="version-date">${highlight(date)}</span>` : ''}
        <span class="version-actions">${renderProviderLinks(filmProviderQuery(title, version.language), version.links, version.providers || film.providers || subsectionProviders)}</span>
      </div>`;
    }).join('');

    return `<div class="entry" data-search="${escapeHtml(searchText)}" data-entry-meta="${escapeHtml(entryMeta)}" data-languages="${escapeHtml(uniqueLanguageKeys.join(' '))}">
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
    const entryYear = releaseYear(date, year);
    return `<div class="entry" data-year="${escapeHtml(entryYear)}" data-search="${escapeHtml(searchText)}">
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
  const FULL_DATE_PATTERN = /^(\d{2})-(\d{2})-(\d{4})$/;

  function entrySortKey(item, isFilm) {
    // Comparable release key: yyyymmdd when a full date exists, yyyy0000
    // otherwise. Films sort by their displayed year (the original release),
    // refined by the original release day when a version provides one.
    if (isFilm) {
      const versions = Array.isArray(item.versions) ? item.versions : legacyVersions(item);
      let baseYear = parseInt(item.year || item.y, 10) || 0;
      if (!baseYear) {
        versions.forEach(version => {
          baseYear = Math.max(baseYear, parseInt(releaseYear(version.date, 0), 10) || 0);
        });
      }
      let monthDay = 0;
      versions.forEach(version => {
        const full = FULL_DATE_PATTERN.exec((version.date || '').toString().trim());
        if (full && +full[3] === baseYear) {
          monthDay = Math.max(monthDay, (+full[2]) * 100 + (+full[1]));
        }
      });
      return baseYear * 10000 + monthDay;
    }
    const full = FULL_DATE_PATTERN.exec((item.date || '').toString().trim());
    if (full) return (+full[3]) * 10000 + (+full[2]) * 100 + (+full[1]);
    return (parseInt(releaseYear(item.date, item.year || item.y), 10) || 0) * 10000;
  }

  function renderSubsection(sub) {
    if (!sub.items || sub.items.length === 0) return '';
    const isFilm = (item) => item.type === 'film' || sub.type === 'films';
    const sortedItems = sub.items.slice().sort((a, b) => entrySortKey(b, isFilm(b)) - entrySortKey(a, isFilm(a)));
    let entriesHtml = '';
    if (sub.type === 'films') {
      entriesHtml = sortedItems.map(item => renderFilmEntry(item, null, sub.providers)).join('');
    } else {
      entriesHtml = sortedItems.map(item => renderListItem(item, sub.providers)).join('');
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
        Direct album and release links can be added in the source JSON files. Generated search links remain available in the main archive while these gaps are filled.
      </p>
      ${renderQualitySubsection('missing-links', 'Missing album / release direct links', missingLinks, 'links')}
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
  const languageContainer = document.getElementById('languages');
  const stickyBar = document.querySelector('.search-bar');
  const cats = [{ id: 'all', label: 'All' }]
    .concat(sections.map(s => ({ id: s.id, label: s.title })))
    .concat([{ id: 'data-quality', label: 'Missing Links / Sources' }]);
  catsContainer.innerHTML = cats.map((c, i) =>
    `<button class="cat-pill ${i === 0 ? 'active' : ''}" type="button" data-cat="${c.id}" aria-pressed="${i === 0 ? 'true' : 'false'}">${escapeHtml(c.label)}</button>`
  ).join('');
  const languages = [{ id: 'all', label: 'All Languages' }].concat(collectLanguages(sections));
  languageContainer.innerHTML = languages.map((language, i) =>
    `<button class="lang-pill ${i === 0 ? 'active' : ''}" type="button" data-language="${escapeHtml(language.id)}" aria-pressed="${i === 0 ? 'true' : 'false'}">${escapeHtml(language.label)}</button>`
  ).join('');
  const yearSelect = document.getElementById('years');
  const years = ['all'].concat(collectYears(sections));
  yearSelect.innerHTML = years.map(year =>
    `<option value="${escapeHtml(year)}">${year === 'all' ? 'All Years' : escapeHtml(year)}</option>`
  ).join('');

  // ---------- Collapsible sections ----------
  function setCollapsed(box, collapsed) {
    box.classList.toggle('collapsed', collapsed);
    const head = box.querySelector(':scope > .section-head, :scope > .sub-head');
    if (head) head.setAttribute('aria-expanded', collapsed ? 'false' : 'true');
  }

  function expandAncestors(el) {
    const subsection = el.closest('.subsection');
    if (subsection) setCollapsed(subsection, false);
    const section = el.closest('.section');
    if (section) setCollapsed(section, false);
  }

  document.querySelectorAll('.section-head, .sub-head').forEach(head => {
    head.setAttribute('role', 'button');
    head.setAttribute('tabindex', '0');
    head.setAttribute('aria-expanded', 'true');
  });

  function toggleCollapseFromEvent(e) {
    const head = e.target.closest('.section-head, .sub-head');
    if (!head || !main.contains(head)) return false;
    const box = head.closest('.section, .subsection');
    if (!box) return false;
    setCollapsed(box, !box.classList.contains('collapsed'));
    return true;
  }

  main.addEventListener('click', (e) => {
    toggleCollapseFromEvent(e);
  });
  main.addEventListener('keydown', (e) => {
    if (e.key !== 'Enter' && e.key !== ' ') return;
    if (e.target.closest('.section-head, .sub-head') && toggleCollapseFromEvent(e)) {
      e.preventDefault();
    }
  });

  function setActiveCategoryButton(categoryId) {
    document.querySelectorAll('.cat-pill').forEach(pill => {
      const isActive = pill.getAttribute('data-cat') === categoryId;
      pill.classList.toggle('active', isActive);
      pill.setAttribute('aria-pressed', isActive ? 'true' : 'false');
    });
  }

  function setActiveLanguageButton(languageId) {
    document.querySelectorAll('.lang-pill').forEach(pill => {
      const isActive = pill.getAttribute('data-language') === languageId;
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
  let activeLang = 'all';
  let activeYear = 'all';
  let activeResultIndex = -1;
  let visibleResults = [];

  // Cache entries and subsections for fast filtering
  const allEntries = Array.from(document.querySelectorAll('.entry'));
  const allSubsections = Array.from(document.querySelectorAll('.subsection'));
  const allSections = Array.from(document.querySelectorAll('.section'));

  function rowMatchesFilters(row) {
    const matchesLanguage = activeLang === 'all' || row.getAttribute('data-language') === activeLang;
    const matchesYear = activeYear === 'all' || row.getAttribute('data-year') === activeYear;
    return matchesLanguage && matchesYear;
  }

  function syncVersionRows(el) {
    const versionRows = Array.from(el.querySelectorAll('.entry-version[data-language]'));
    if (!versionRows.length) {
      if (activeLang !== 'all') return false;
      return activeYear === 'all' || (el.getAttribute('data-year') || '') === activeYear;
    }

    let visibleRows = 0;
    versionRows.forEach(row => {
      const matches = rowMatchesFilters(row);
      row.classList.toggle('hidden', !matches);
      if (matches) visibleRows++;
    });

    return (activeLang === 'all' && activeYear === 'all') || visibleRows > 0;
  }

  function entrySearchText(el) {
    if (activeLang === 'all' && activeYear === 'all') return el.getAttribute('data-search') || '';

    const versionRows = Array.from(el.querySelectorAll('.entry-version[data-language]'));
    if (!versionRows.length) return el.getAttribute('data-search') || '';
    const matchingRows = versionRows.filter(rowMatchesFilters);
    if (!matchingRows.length) return '';
    return (
      matchingRows.map(row => row.getAttribute('data-search') || row.textContent || '').join(' ') +
      ' ' +
      (el.getAttribute('data-entry-meta') || '')
    ).toLowerCase();
  }

  function syncResultNav() {
    const hasScopedResults = visibleResults.length > 0 && (currentQuery || activeCat !== 'all' || activeLang !== 'all' || activeYear !== 'all');
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
      expandAncestors(activeResult);
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
      const matchesLanguage = syncVersionRows(el);
      const text = entrySearchText(el);
      const matchesQuery = !query || text.indexOf(query) !== -1;
      if (matchesLanguage && matchesQuery) {
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
    clearBtn.hidden = (!query && activeCat === 'all' && activeLang === 'all' && activeYear === 'all');
    visibleResults = allEntries.filter(el => {
      if (el.classList.contains('hidden')) return false;
      const section = el.closest('.section');
      return section && !section.classList.contains('hidden');
    });

    if (visibleResults.length > 0 && (query || activeCat !== 'all' || activeLang !== 'all' || activeYear !== 'all')) {
      const retainedIndex = previousActive ? visibleResults.indexOf(previousActive) : -1;
      const nextIndex = retainedIndex >= 0 ? retainedIndex : 0;
      setActiveResult(nextIndex, Boolean(options.scrollToFirst && query && query !== previousQuery));
    } else {
      setActiveResult(-1, false);
    }

    // empty state
    const allHidden = !Array.from(document.querySelectorAll('.section')).some(s => !s.classList.contains('hidden'));
    empty.classList.toggle('show', allHidden && (query || activeCat !== 'all' || activeLang !== 'all' || activeYear !== 'all'));

    // While searching, surface matches hidden inside collapsed boxes.
    if (query) {
      allSections.forEach(sec => {
        if (!sec.classList.contains('hidden') && sec.querySelector('.entry:not(.hidden)')) setCollapsed(sec, false);
      });
      allSubsections.forEach(sub => {
        if (!sub.classList.contains('hidden') && sub.querySelector('.entry:not(.hidden)')) setCollapsed(sub, false);
      });
    }

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
    const selectors = '.entry:not(.hidden) .entry-title, .entry:not(.hidden) .entry-note, .entry:not(.hidden) .entry-version:not(.hidden) .version-title, .entry:not(.hidden) .entry-version:not(.hidden) .version-date, .entry:not(.hidden) .missing-list';
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
    activeLang = 'all';
    activeYear = 'all';
    setActiveCategoryButton(activeCat);
    setActiveLanguageButton(activeLang);
    yearSelect.value = 'all';
    yearSelect.classList.remove('active');
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
        setCollapsed(target, false);
        const stickyOffset = stickyBar ? stickyBar.offsetHeight + 24 : 120;
        const top = target.getBoundingClientRect().top + window.pageYOffset - stickyOffset;
        window.scrollTo({ top, behavior: 'smooth' });
      }
    } else {
      window.scrollTo({ top: 0, behavior: 'smooth' });
    }
  });

  languageContainer.addEventListener('click', (e) => {
    const btn = e.target.closest('.lang-pill');
    if (!btn) return;
    activeLang = btn.getAttribute('data-language');
    setActiveLanguageButton(activeLang);
    applyFilter({ scrollToFirst: true });
  });

  yearSelect.addEventListener('change', () => {
    activeYear = yearSelect.value || 'all';
    yearSelect.classList.toggle('active', activeYear !== 'all');
    applyFilter({ scrollToFirst: true });
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

  initAnalyticsNotice();
  start();
})();
