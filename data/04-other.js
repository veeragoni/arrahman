// ============================================================================
// 04 — LABELS, INITIATIVES, FOUNDATION, MUSIC SUPERVISION, GUEST WORK, BOOKS
// ============================================================================

// ============================================================================
// SECTION 8: NON-CREATIVE WORK
// ============================================================================

const LABELS = [
  { title: "KM Musiq" },
  { title: "Qyuki" },
  { title: "YM Movies" },
  { title: "A.R. Rahman App" },
  { title: "AR X AR App" },
  { title: "www.arrahman.com" },
  { title: "ARR Studios" },
  { title: "ARR Immersive Entertainment" },
  { title: "Ustream" },
  { title: "AR-Rahman Limited" },
];

const INITIATIVES_SELF = [
  { title: "KM Music Conservatory (KMMC)" },
  { title: "KMMC — Middlesex University Music Degree Collaboration" },
  { title: "JBL — KMMC Sound Scholarship" },
  { title: "AR Rahman & Firdaus Studio", year: 2024 },
  { title: "The Dharavi Dream Project (Qyuki)" },
  { title: "NAFS (Qyuki)" },
  { title: "Qutub-E-Kripa" },
  { title: "KM Sufi Ensemble" },
  { title: "Ahhaa App — KMMC Collaboration" },
  { title: "The Berklee — A. R. Rahman Scholarship" },
  { title: "Apple — KMMC Scholarship" },
  { title: "MAC — KMMC Lab" },
  { title: "Nagaland's CM Music Scholarship — TaFMA — KMMC" },
  { title: "KMMC Bharat Maestro Awards" },
  { title: "Indian Classical Music Ensemble — Jhaala Rahman" },
  { title: "All Women Sufi Music Ensemble — Rooh-e-Noor" },
  { title: "Ta Futures", note: "Announced" },
  { title: "Katraar", note: "Announced" },
];

const RAHMAN_FOUNDATION = [
  { title: "The Sunshine Orchestra (Chennai)" },
  { title: "One Heart Foundation" },
  { title: "The Sunshine Orchestra (Nagaland)" },
  { title: "Futureproof", note: "Announced" },
];

const FOUNDATION_SUPPORT = [
  { title: "MGR Higher Secondary School" },
  { title: "SlumGods" },
  { title: "Faizal & Shabana Foundation" },
  { title: "IIMUN" },
  { title: "Internshala — Intern with Icon (IwI)", year: 2019 },
  { title: "Firdaus Women's Orchestra — Expo 2020 Dubai" },
  { title: "Firdaus Studio & Music Lab — Expo 2020 Dubai" },
  { title: "HBAR Foundation" },
  { title: "Firdaus Orchestral Qawwali Project" },
  { title: "Nita Mukesh Ambani Cultural Centre (NMACC)" },
  { title: "JBL Music Academy" },
  { title: "Tulah Clinical Wellness" },
  { title: "Rooh Records with Warner Music" },
  { title: "Dolly J Studio", year: 2025 },
];

const MISCELLANEOUS = [
  { title: "Peace Garden" },
  { title: "Hajiyani Kareema's Kitchen" },
];

const MS_FILM_OST = [
  { title: "Lake of Fire", year: 2017 },
  { title: "Nanak Shah Fakir", year: 2018 },
  { title: "Firdaus Studio Performances", year: 2022 },
];

const MS_NONFILM_ALBUMS = [
  { title: "Ooh La La La (Tamil)", year: 2007 },
  { title: "Ooh La La La (Telugu)", year: 2007 },
  { title: "Rhyme Skool with Katrina Kaif Vol. 1", year: 2010 },
  { title: "Rhyme Skool with Katrina Kaif Vol. 2", year: 2011 },
  { title: "Call Me Rashid", year: 2012 },
  { title: "Navaratna", year: 2015 },
  { title: "Kuhu Kuhu", year: 2023 },
  { title: "Kunangudi Mastan Sahib Sufi Album (C&U)" },
];

const MS_FEATURE_FILM = [
  { title: "Atkan Chatkan", year: 2020 },
];

const MS_DOCUMENTARY = [
  { title: "Bismillah Of Benaras", year: 2014 },
  { title: "Cinema Veeran", year: 2017 },
];

const MS_TV_WEB = [
  { title: "Mission Ustad", year: 2007 },
  { title: "Everest", year: 2014 },
  { title: "Jammin S01", year: 2016, note: "Qyuki" },
  { title: "Project X", year: 2016, note: "Qyuki" },
  { title: "Jammin S02", year: 2018, note: "Qyuki" },
  { title: "Arrived", year: 2018 },
  { title: "Haq Se Hip Hop", year: 2019, note: "Qyuki" },
  { title: "NEXA Music Lounge", year: 2020 },
];

const MS_CONCERTS = [
  { title: "Qyuki Mixer", year: 2019 },
  { title: "Haq Se Hip Hop Hindustan Concert", year: 2019, note: "Qyuki" },
  { title: "Epic Fam Jam", year: 2020, note: "Qyuki" },
];

const MS_SHORT_FILMS = [
  { title: "Indian Legends", year: 2001 },
  { title: "Thaalam — Rhythm of Nation", year: 2019 },
  { title: "Triumph Of Nithila", year: 2018 },
];

const GUEST_FILMS = [
  { title: "Kadhal Virus", year: 2002 },
  { title: "Mission Mangal", year: 2019, note: "Film Character" },
  { title: "Aaraattu", year: 2021 },
];

const GUEST_DOCS = [
  { title: "Chotta Muthal Chudala Vare", year: 2003 },
  { title: "Bollywood Indiens Kligendes Keno", year: 2005 },
  { title: "Son of a Preacherman", year: 2010, note: "Promos only" },
  { title: "The Nation's Favourite Dance Moment", year: 2013 },
  { title: "The Distortion of Sound", year: 2014 },
  { title: "A Tribute to Aadesh Shrivasatava", year: 2016 },
  { title: "Roots", year: 2016 },
  { title: "National Geographic Mega Icons", year: 2020 },
  { title: "The Journey of India", year: 2022 },
  { title: "The Reinvent Series", year: 2023 },
  { title: "From Headhunting to Beatboxing — The Naga Story", year: 2025 },
];

const GUEST_TV_RADIO = [
  { title: "L'Oeil Du Cyclone", year: 1997 },
  { title: "India Rocks", year: 2007 },
  { title: "Aahaa FM Rahmania", year: 2007 },
  { title: "Champions with A. R. Rahman", year: 2016 },
  { title: "The A. R. Rahman Show", year: 2021 },
  { title: "I Love ARR Podcast", year: 2020, note: "2020–" },
  { title: "Rahman Music Sheets", year: 2021, note: "2021–" },
];

const GUEST_CONCERT_FILMS = [
  { title: "Soundtrack of our Lives", year: 2020 },
];

const GUEST_MUSIC_VIDEOS = [
  { title: "Akon's Beautiful (Freedom)", year: 2009 },
];

const GUEST_AD_PROMO = [
  { title: "Airtel Music on Demand", year: 2007 },
  { title: "Nokia Xpress Music", year: 2008 },
  { title: "Airtel DTH / Digital TV", year: 2009 },
  { title: "Marcodi's Harpejji", year: 2010 },
  { title: "Union Bank of India", year: 2011 },
  { title: "ROLI's Seaboard RISE", year: 2015 },
  { title: "Zuka Chocolate Café", year: 2016 },
  { title: "Casio", year: 2017 },
  { title: "Apple Music AirPods", year: 2017 },
  { title: "Apple Mac", year: 2018 },
  { title: "Apple iPhone X", year: 2018 },
  { title: "ROLI's Colours of India Soundpack", year: 2018 },
  { title: "iPhone 11", year: 2019 },
  { title: "Dolby Atmos in Apple Music", year: 2021 },
  { title: "Canon India", year: 2022 },
  { title: "Sea Board RISE 2", year: 2022 },
  { title: "Expressive Osmose", year: 2023 },
  { title: "Spotify Premium", year: 2023 },
  { title: "JWC", year: 2023 },
  { title: "Macbook Pro M2 Max", year: 2023 },
  { title: "JBL Authentics", year: 2024 },
  { title: "Sonorium Zomato", year: 2025 },
  { title: "JBL Tour Pro 3 Earbuds", year: 2025 },
  { title: "50 Years of Apple", year: 2026 },
];

const GUEST_CAUSES = [
  { title: "UN MDG End Poverty 2015", year: 2005 },
  { title: "UN MDG End Poverty 2015", year: 2008 },
  { title: "UN MDG Stand Up Take Action End Poverty 2015", year: 2008 },
  { title: "End Polio Now", year: 2014 },
  { title: "UN GGSD We The People", year: 2015 },
  { title: "UN GGSD — Big Magic Quality Education", year: 2015 },
  { title: "UN GGSD — Hello Mag The Power of Giving", year: 2015 },
  { title: "NDTV — Piramal Group Cultivating Hope", year: 2016 },
  { title: "Income Tax Declaration Scheme", year: 2016 },
  { title: "Save an Orphan", year: 2016 },
  { title: "BTC World Blood Cancer Day For Indians By Indians", year: 2017 },
  { title: "The Quint Letter to India", year: 2018 },
  { title: "TNC Chennai Wetlands Restoration", year: 2019 },
  { title: "COVID-19 Crisis — Words of Encouragement", year: 2020 },
  { title: "Class of 2020 India", year: 2020 },
  { title: "Water Matters", year: 2020 },
  { title: "Mission Paani Water Warrior", year: 2020 },
  { title: "The Hans Foundation Mental Health", year: 2020 },
  { title: "The Ability Foundation Inclusive Education", year: 2020 },
  { title: "Alert NGO Save Lives", year: 2020 },
  { title: "Tamil Nadu Elections Voting Rights", year: 2021 },
  { title: "Film Heritage Foundation Film Preservation", year: 2021 },
  { title: "Bharatiya Vidya Bhavan US Mission's Support", year: 2021 },
  { title: "ILO-JMI MACL Competition", year: 2021 },
  { title: "Covid-19 Vaccination", year: 2021 },
  { title: "IIMUN Lok Sabha Elections My First Vote", year: 2024 },
  { title: "IIMUN Lok Sabha Elections My Vote My Voice", year: 2024 },
  { title: "World Para Athletics Championships", year: 2025 },
  { title: "Voice Against the Voiceless", year: 2026 },
];

const OTHERS = [
  { title: "Cosmopolitan Mag February — Shoot Director ft. Khatija Rahman", year: 2021 },
];

const BOOKS_SELF = [
  { title: "India Matters — Shyam Goenka and VM Badola", year: 1998 },
  { title: "Icons from the World of Arts — Ranjitha Ashok", year: 2004 },
  { title: "Face to Face India — Conversations with Karan Thapar", year: 2006 },
  { title: "Nineteen Hours and Fourteen Minutes — James Gooding", year: 2009 },
  { title: "Oru Kanavin Isai (Vikatan Prasuram) — Krishna Davinci", year: 2009 },
  { title: "Oscar Nayagan A R Rahman — Sabitha Joseph", year: 2009 },
  { title: "Oscar Winner A. R. Rahman 100 — Sabitha Joseph", year: 2009 },
  { title: "Jai Ho AR Rahman — N Chokkan", year: 2009 },
  { title: "Musical Storm — Kamini Mathai", year: 2009 },
  { title: "A Journey Down Memory Lane — Raju Bharatan", year: 2010 },
  { title: "Global Indians — The Times of India Group", year: 2011 },
  { title: "Flashback — The Times of India Group", year: 2011 },
  { title: "The Spirit of Music — Nasreen Munni Kabhir (NMK)", year: 2011 },
  { title: "Ananda Vikatan — Pokkisham — Vikatan Pirasuram", year: 2011 },
  { title: "The Spirit of Music — Additional Chapters (NMK)", year: 2017 },
  { title: "Bollywood's 70 Iconic Power Brands — Rajita & Arindam Chaudhuri", year: 2017 },
  { title: "Bollywood — The Films! The Songs! The Stars! — DK", year: 2017 },
  { title: "Namste A. R. Rahman — Sunanda Verma & Carolin Spannuth", year: 2018 },
  { title: "Notes of a Dream — Krishna Trilok", year: 2018 },
  { title: "Naveena Indhiya Thiriraiyisaiyan Adaiyallam — Vijay Mahendran", year: 2019 },
  { title: "Beyond Rahman: Culture Globally — Rupa Chakravarti", year: 2024 },
  { title: "Role Models — Shehla Rashid", year: 2024 },
  { title: "World's Greatest Musicians — Wonder House Books", year: 2024 },
  { title: "Against the Grain — Pankaj Mishra", year: 2024 },
];

const BOOKS_FOR_OTHERS = [
  { title: "Fathers & Sons — Anjali Vinal Ambani and Amar Vimal Ambani", year: 2009, note: "Featurette" },
  { title: "TIME Magazine 100 featuring Chetan Bhagat", year: 2010, note: "Profile Writer" },
  { title: "Glimpses of Indian Autographs — Praful Thakkar", year: 2011, note: "Celebrity Autograph Featurette" },
  { title: "Conversations with Maniratnam — Bharadwaj Rangan", year: 2012, note: "Foreword" },
  { title: "TIME Magazine 100 featuring Aamir Khan", year: 2013, note: "Profile Writer" },
  { title: "Oscars Notebook", year: 2016, note: "Celebrity Message" },
  { title: "The Rule of One — Narayan Sundararajan & Others", year: 2019, note: "Review Notes" },
  { title: "Nagaland Hornbill Festival Photo Book", year: 2019, note: "Photo Featurette" },
  { title: "Nagme, Kisse, Baatein, Yaadein — Rakesh Anand Bakshi", year: 2021, note: "Experiences" },
  { title: "The Stranger in the Mirror — Rakeysh OMP Mehra", year: 2021, note: "Foreword" },
  { title: "Festival Beyond Borders — LGMF", year: 2023, note: "Guest Appearance" },
];

const FOUNDATION_MERCH = [
  { title: "Pray For Me Brother Colouring Books Vol. 1–5", year: 2007 },
  { title: "A. R. Rahman Foundation Calendar", year: 2009 },
  { title: "A. R. Rahman Foundation Calendar", year: 2010 },
  { title: "Reflections Coffee Table Book", year: 2013 },
  { title: "Wonderment World Tour Merchandise", year: 2025 },
];
