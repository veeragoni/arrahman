// ============================================================================
// SECTION MANIFEST
// This file assembles all data arrays into the SECTIONS structure that
// drives the UI. If you add a brand-new category, add an entry here.
// ============================================================================

// ============================================================================
// SECTIONS — assembles everything for the UI
// ============================================================================

const SECTIONS = [
  {
    id: 'films',
    num: '01',
    title: 'Film Compositions',
    blurb: 'Multi-language releases — Tamil, Telugu, Hindi, Malayalam and others. Each entry shows the title and release date for every language version.',
    subsections: [
      { id: 'films-main', num: '1–5', title: 'Films with multi-language releases', type: 'films', items: FILMS },
      { id: 'tamil-undubbed', num: '1.1', title: 'Tamil Undubbed', type: 'list', items: TAMIL_UNDUBBED },
      { id: 'telugu-undubbed', num: '2.1', title: 'Telugu Undubbed', type: 'list', items: TELUGU_UNDUBBED },
      { id: 'hindi-undubbed', num: '3.1', title: 'Hindi Undubbed', type: 'list', items: HINDI_UNDUBBED },
      { id: 'malayalam-undubbed', num: '4.1', title: 'Malayalam Undubbed', type: 'list', items: MALAYALAM_UNDUBBED },
      { id: 'foreign-ost', num: '5.1', title: 'Foreign Language OST', type: 'list', items: FOREIGN_OST },
      { id: 'chinese', num: '5.2', title: 'Chinese', type: 'list', items: CHINESE_FILMS },
      { id: 'persian-arabic', num: '5.3', title: 'Persian / Arabic', type: 'list', items: PERSIAN_ARABIC },
      { id: 'urdu', num: '5.4', title: 'Urdu', type: 'list', items: URDU_FILMS },
      { id: 'film-instrumentals', num: '4.2', title: 'Film Instrumentals', type: 'list', items: FILM_INSTRUMENTALS },
      { id: 'bgm-score', num: '4.3', title: 'BGM Score / OST', type: 'list', items: BGM_SCORE },
      { id: 'forthcoming', num: '—', title: 'Forthcoming — In Progress', type: 'list', items: FORTHCOMING },
      { id: 'announced', num: '—', title: 'Announced Projects', type: 'list', items: ANNOUNCED_PROJECTS },
      { id: 'no-updates', num: '—', title: 'Projects — No Latest Updates', type: 'list', items: NO_UPDATES },
    ]
  },
  {
    id: 'nonfilm',
    num: '06',
    title: 'Non-Film Compositions',
    blurb: 'Albums, collaborations, TV and web series, singles, short films, immersive works, stage musicals and theme songs spanning four decades.',
    subsections: [
      { id: 'albums', num: '6.1', title: 'Albums / Collaborations', type: 'list', items: ALBUMS_COLLAB },
      { id: 'tv-web', num: '6.2', title: 'TV / Web Series', type: 'list', items: TV_WEB_SERIES },
      { id: 'singles', num: '6.3', title: 'Singles', type: 'list', items: SINGLES },
      { id: 'featured', num: '6.4', title: 'Featured in the work of other artistes', type: 'list', items: FEATURED_IN_OTHERS },
      { id: 'docs-collab', num: '6.5', title: 'Documentaries / Concert Films / Collaborations', type: 'list', items: DOCUMENTARIES_COLLAB },
      { id: 'shortfilms', num: '6.6', title: 'Short Films', type: 'list', items: SHORT_FILMS },
      { id: 'vr', num: '6.7', title: 'VR Films / Immersive Films', type: 'list', items: VR_FILMS },
      { id: 'musicals', num: '6.8', title: 'Stage Musicals', type: 'list', items: STAGE_MUSICALS },
      { id: 'signatures', num: '6.9', title: 'Signature + Theme Songs', type: 'list', items: SIGNATURES_THEMES },
    ]
  },
  {
    id: 'ads',
    num: '07',
    title: 'Advertisements & Ringtones',
    blurb: 'A long career soundtracking Indian advertising — from Allwyn watches in the 1980s to Yamaha and Apple in 2026.',
    subsections: [
      { id: 'ads-pre', num: '7.1.1', title: 'Advertisements — pre-2000', type: 'list', items: ADS_PRE_2000 },
      { id: 'ads-post', num: '7.1.2', title: 'Advertisements — post-2000', type: 'list', items: ADS_POST_2000 },
      { id: 'ringtones', num: '7.2', title: 'Ringtones', type: 'list', items: RINGTONES },
    ]
  },
  {
    id: 'noncreative',
    num: '08',
    title: 'Other Work, Institutions & Curation',
    blurb: 'Labels, conservatories, foundations, the Firdaus initiatives, music supervision, and guest appearances — work beyond composing.',
    subsections: [
      { id: 'labels', num: '8.1', title: 'Labels', type: 'list', items: LABELS },
      { id: 'initiatives', num: '8.2', title: 'Initiatives (Self)', type: 'list', items: INITIATIVES_SELF },
      { id: 'foundation', num: '8.3', title: 'A. R. Rahman Foundation', type: 'list', items: RAHMAN_FOUNDATION },
      { id: 'foundation-support', num: '8.3.1', title: 'Foundation — Support for Others', type: 'list', items: FOUNDATION_SUPPORT },
      { id: 'misc', num: '8.4', title: 'Miscellaneous', type: 'list', items: MISCELLANEOUS },
      { id: 'ms-film-ost', num: '8.5.1', title: 'Music Supervisor — Film OST', type: 'list', items: MS_FILM_OST },
      { id: 'ms-nonfilm', num: '8.5.2', title: 'Music Supervisor — Non-Film Albums', type: 'list', items: MS_NONFILM_ALBUMS },
      { id: 'ms-feature', num: '8.5.3', title: 'Music Supervisor — Feature Film', type: 'list', items: MS_FEATURE_FILM },
      { id: 'ms-doc', num: '8.5.4', title: 'Music Supervisor — Documentary', type: 'list', items: MS_DOCUMENTARY },
      { id: 'ms-tv', num: '8.5.5', title: 'Music Supervisor — TV / Web Series', type: 'list', items: MS_TV_WEB },
      { id: 'ms-concerts', num: '8.5.6', title: 'Music Supervisor — Concerts / Interactive Sessions', type: 'list', items: MS_CONCERTS },
      { id: 'ms-short', num: '8.5.7', title: 'Music Supervisor — Short Films', type: 'list', items: MS_SHORT_FILMS },
      { id: 'guest-films', num: '8.6.1', title: 'Guest / Special Appearances — Films', type: 'list', items: GUEST_FILMS },
      { id: 'guest-docs', num: '8.6.2', title: 'Guest / Special Appearances — Documentaries', type: 'list', items: GUEST_DOCS },
      { id: 'guest-tv', num: '8.6.3', title: 'Guest / Special Appearances — TV / Radio / Web Series', type: 'list', items: GUEST_TV_RADIO },
      { id: 'guest-concerts', num: '8.6.4', title: 'Guest / Special Appearances — Concert Films', type: 'list', items: GUEST_CONCERT_FILMS },
      { id: 'guest-mv', num: '8.6.5', title: 'Guest / Special Appearances — Music Videos', type: 'list', items: GUEST_MUSIC_VIDEOS },
      { id: 'guest-ads', num: '8.6.7', title: 'Guest / Special Appearances — Ad / Promotional Films', type: 'list', items: GUEST_AD_PROMO },
      { id: 'guest-causes', num: '8.6.8', title: 'Campaigns for Causes', type: 'list', items: GUEST_CAUSES },
      { id: 'others', num: '8.7', title: 'Others', type: 'list', items: OTHERS },
      { id: 'books-self', num: '8.8.1', title: 'Books & Literature (Self)', type: 'list', items: BOOKS_SELF },
      { id: 'books-others', num: '8.8.2', title: 'Books & Literature (For Others)', type: 'list', items: BOOKS_FOR_OTHERS },
      { id: 'foundation-merch', num: '8.8.3', title: 'A. R. Rahman Foundation — Merchandise', type: 'list', items: FOUNDATION_MERCH },
    ]
  },
  {
    id: 'videos',
    num: '09',
    title: 'Video Song Performances',
    blurb: 'On-camera music release performances and music videos — across film and non-film work.',
    subsections: [
      { id: 'videos-film', num: '9.1', title: 'Video of Film Songs', type: 'list', items: VIDEOS_FILM },
      { id: 'videos-nonfilm', num: '9.2', title: 'Video of Non-Film Songs (Singles)', type: 'list', items: VIDEOS_NONFILM },
    ]
  },
];

// Expose for app.js
window.SECTIONS = SECTIONS;
