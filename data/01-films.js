// ============================================================================
// 01 — FILM COMPOSITIONS
// To add a film: copy a row, fill in the language fields that apply.
//   t  = Tamil   te = Telugu   h = Hindi   m = Malayalam   o = Other
//   y  = year (number)         note = optional note string
//   Use the format "Title • DD-MM-YYYY" or "Title • YYYY"
// ============================================================================

// Helper for film rows (multi-language releases of the same film)
// Each row: { y: year, t: tamil, te: telugu, h: hindi, m: malayalam, o: other }
// Where each language field is "Title • date" or null

const FILMS = [
  // === 1992 ===
  { y: 1992, t: "Roja • 15-08-1992", te: "Roja • 1992", h: "Roja • 1994", m: "Roja • 1995", o: "Roja (Marathi) • 1996" },
  { y: 1992, t: "Asokan • 1994", te: "Yoddha • 1992", h: "Dharam Yoddha • 1996", m: "Yodha (Malayalam) • 03-09-1992" },
  // === 1993 ===
  { y: 1993, t: "Puthiya Mugam • 28-05-1993", te: "Padmavyuham • 1993", h: "Vishwa Vidhaata • 1997" },
  { y: 1993, t: "Gentleman • 1993", te: "Gentleman • 1994", h: "The Gentleman • 1996", note: "Note: dub" },
  { y: 1993, t: "Kizhakku Cheemaiyile • 13-11-1993", te: "Palanaati Pourusham • 1994" },
  { y: 1993, t: "Thiruda Thiruda • 13-11-1993", te: "Donga Donga • 1994", h: "Chor Chor • 1996" },
  // === 1994 ===
  { y: 1994, t: "Vandicholai Chinnaraasu • 15-04-1994", te: "Bobbili Paaparayudu • 1996" },
  { y: 1994, t: "Duet • 20-05-1994", te: "Duet • 1994", h: "Tu Hi Mera Dil • 1995" },
  { y: 1994, t: "Super Police • 1995", te: "Super Police • 23-06-1994", h: "Khel Khiladi Ka • 1998" },
  { y: 1994, t: "Manitha Manitha • 1995", te: "Gang Master • 15-07-1994" },
  { y: 1994, t: "May Madham • 09-09-1994", te: "Hrudayaanjai • 1994" },
  { y: 1994, t: "Kadhalan • 17-09-1994", te: "Premikudu • 1994", h: "Hum Se Hain Muqabla • 1995" },
  { y: 1994, t: "Karuthamma • 03-11-1994", te: "Vanitha / Aada Brathuku / Osey Krishnamma • 1995" },
  // === 1995 ===
  { y: 1995, t: "Bombay • 10-03-1995", te: "Bombay • 1995", h: "Bombay • 1995" },
  { y: 1995, t: "Indira • 11-05-1995", te: "Indira • 1996", h: "Priyanka • 1996" },
  { y: 1995, t: "Rangeela • 1995", te: "Rangeli • 1995", h: "Rangeela • 08-11-1995" },
  { y: 1995, t: "Muthu • 23-10-1995", te: "Muthu • 1995", h: "Muthu Maharaja • 1998" },
  { y: 1995, t: "Indian • 09-05-1995", te: "Bharatheeyudu • 1996", h: "Hindusthani • 1996" },
  // === 1996 ===
  { y: 1996, t: "Love Birds • 15-01-1996", te: "Love Birds • 1996", h: "Love Birds • 1996" },
  { y: 1996, t: "Kaadhal Desam • 23-08-1996", te: "Prema Desam • 1996", h: "Duniya Dil Waalon ki • 1997" },
  { y: 1996, t: "Mr Romeo • 10-11-1996", te: "Mr Romeo • 1996", h: "Mr Romeo • 1997" },
  // === 1997 ===
  { y: 1997, t: "Minsara Kanavu • 14-01-1997", te: "Merupu Kalalu • 1997", h: "Sapnay • 1997" },
  { y: 1997, t: "Iruvar • 14-01-1997", te: "Iddaru • 1997" },
  { y: 1997, t: "Ottam • 1997", te: "50-50 • 1997", h: "Daud • 22-08-1997" },
  { y: 1997, t: "Ratchagan • 30-10-1997", te: "Rakshakudu • 1998", h: "Fire • 05-11-1998" },
  { y: 1997, t: "Monalisa • 1997", h: "Kabhi Na Kabhi • 17-04-1998" },
  // === 1998 ===
  { y: 1998, t: "Jeans • 24-04-1998", te: "Jeans • 1998", h: "Jeans • 1998" },
  { y: 1998, t: "Uyire • 1998", te: "Prematho • 1998", h: "Dil se • 21-08-1998" },
  { y: 1998, h: "1947 Earth • 10-09-1999" },
  { y: 1998, h: "Pukar • 04-02-2000" },
  // === 1999 ===
  { y: 1999, t: "Jodi • 1999", te: "Jodi • 1999", h: "Doli Sajake Rakhna • 27-11-1998", o: "Sajni (Kannada) • 2007" },
  { y: 1999, t: "En Swasa Katrae • 26-02-1999", te: "Premante Pranamistha • 1999", h: "Zubeidaa • 19-01-2001" },
  { y: 1999, t: "Padaiyappa • 10-04-1999", te: "Narasimha • 1999", h: "One 2 Ka 4 • 30-03-2001" },
  { y: 1999, t: "Kadhalar Dhinam • 09-07-1999", te: "Premikula Roju • 1999", h: "Dil Hi Dil Mein • 1999" },
  { y: 1999, t: "Thalam • 1999", h: "Taal • 13-08-1999" },
  { y: 1999, t: "Mudhalvan • 07-11-1999", te: "Oke Okkadu • 1999", h: "Nayak • 2001" },
  { y: 1999, h: "Thakshak • 03-12-1999" },
  { y: 1999, h: "Lagaan • 15-06-2001" },
  { y: 1999, h: "The Legend Of Bhagath Singh • 07-06-2002" },
  { y: 1999, h: "Tehzeeb • 21-11-2003" },
  // === 2000 ===
  { y: 2000, t: "Alai Payuthey • 14-04-2000", te: "Sakhi • 2000", h: "Saathiya • 20-12-2002" },
  { y: 2000, t: "Kandukondain Kandukondain • 05-05-2000", te: "Priyuralu Pilichindhi • 2000", h: "Lakeer • 14-05-2004" },
  { y: 2000, t: "Rhythm • 15-09-2000", te: "Rhythm • 2000", h: "Meenaxi: A Tale of 3 Cities • 02-04-2004" },
  { y: 2000, t: "Thenaali • 26-10-2000", te: "Tenali • 2000", h: "Bose: The Forgotten Hero • 13-05-2005" },
  // === 2001 ===
  { y: 2001, t: "Star • 27-07-2001", te: "Takkari Donga Chakkani Chukka • 2005", h: "Mangal Pandey: The Rising • 12-08-2005" },
  { y: 2001, t: "Paarthaale Parvasam • 14-11-2001", te: "Paravasam • 2000", h: "Water • 09-09-2005" },
  // === 2002 ===
  { y: 2002, t: "Kannathil Muthamittal • 14-02-2002", te: "Amritha • 2002", h: "Rang De Basanti • 27-01-2006" },
  { y: 2002, t: "Baba • 15-08-2002", te: "Baba • 2002", h: "Ada • 31-12-2010", o: "Baba (Kannada) • 10-12-2025" },
  // === 2003 ===
  { y: 2003, t: "Parasuram • 30-05-2003", te: "Police Karthavyam • 2003", h: "Ghajini • 25-12-2008" },
  { y: 2003, t: "Boys • 29-08-2003", te: "Boys • 2003", h: "Boys • 2012", note: "Hindi: Jaane Tu Ya Jaane Naa • 04-07-2008" },
  { y: 2003, t: "Enakku 20 Unakku 18 • 19-12-2003", te: "Nee Manasu Naaku Telusu • 2005", h: "Yuvvraaj • 21-11-2008" },
  // === 2004 ===
  { y: 2004, t: "Aayutha Ezhuthu • 21-05-2004", te: "Yuvaa • 2004", h: "Yuvaa • 2004 (Hindi dub) / Delhi 6 • 20-02-2009" },
  { y: 2004, t: "New • 09-07-2004", te: "Naani • 14-05-2004", h: "Jhoota Hi Sahi • 22-10-2010" },
  { y: 2004, h: "Swades • 17-12-2004", te: "Desam • 2005" },
  { y: 2004, h: "Kisna • 21-01-2004", te: "Kisna • 2005" },
  { y: 2004, h: "Rockstar • 11-11-2011" },
  { y: 2004, h: "Jab Tak Hai Jaan • 13-11-2012" },
  { y: 2004, h: "Highway • 21-02-2014" },
  { y: 2004, h: "Lekar Hum Deewana Dil • 04-07-2014" },
  { y: 2004, h: "Tamasha • 27-11-2015" },
  { y: 2004, h: "Mohenjodaro • 12-08-2016" },
  { y: 2004, h: "Sanju • 29-06-2018", note: "2 tracks" },
  { y: 2004, h: "Love Sonia • 06-09-2019", note: "1 track" },
  { y: 2004, h: "The Fakir Of Venice • 08-12-2019" },
  { y: 2004, h: "Dil Bechara • 24-07-2020", o: "Mimi (Hindi) • 26-07-2021" },
  { y: 2004, h: "Heropanti 2 • 29-04-2022" },
  { y: 2004, h: "Mili • 04-11-2022" },
  { y: 2004, h: "Gandhi Vs Godse – Ek Yudh • 26-01-2023" },
  { y: 2004, h: "Pippa • 07-11-2023" },
  { y: 2004, h: "Amar Singh Chamkila • 26-03-2024" },
  { y: 2004, h: "Ramayana (Introduction) • 04-07-2025" },
  { y: 2004, h: "Uff Yeh Siyapaa • 12-09-2025" },
  { y: 2004, h: "Main Vapas Aaunga", note: "Singles released" },
  // === 2006-2007 ===
  { y: 2006, t: "Jillunu Oru Kaadhal / SOK • 08-09-2006", te: "Nuvvu Nenu Prema • 2006" },
  { y: 2006, t: "Varalaru / God Father • 20-10-2006", te: "God Father • 2012", o: "God Father (2012) Kannada" },
  { y: 2007, t: "Guru • 2007", te: "Gurukanth • 2006", h: "Guru • 12-01-2007" },
  { y: 2007, t: "Provoked • 2007", h: "Provoked • 06-04-2007", note: "English film" },
  { y: 2007, t: "Shivaji The Boss • 15-06-2007", te: "Shivaji The Boss • 2007", h: "Shivaji The Boss • 2010", o: "Mahamuduru (2010)" },
  { y: 2007, t: "Azhagiya Tamizh Magan • 08-11-2007" },
  { y: 2007, t: "Prem Nagar • 2007", te: "Aye Taxi • 2007", m: "Love • 2007 (Malayalam)", o: "Kannada dub" },
  // === 2008 ===
  { y: 2008, t: "Jodhaa Akbar • 2008", te: "Jodhaa Akbar • 2008", h: "Jodhaa Akbar • 15-02-2008" },
  { y: 2008, t: "Naanum Kodesiwaran • 2008", te: "Slumdog Crorepathi • 2008", h: "Slumdog Millionaire (OST) • 25-12-2008", note: "Dub edits / OST" },
  // === 2009-2010 ===
  { y: 2009, t: "Blue • 2011", h: "Blue • 16-10-2009" },
  { y: 2010, t: "Vinnaithaandi Varuvaaya • 26-02-2010", te: "Ye Maaya Chesave • 2010", h: "Ekk Dewanaa Thhaa • 17-02-2012" },
  { y: 2010, t: "Raavanan • 2010", te: "Villian • 2010", h: "Raavan • 18-06-2010" },
  { y: 2010, t: "Enthiran • 01-10-2010", te: "Robot • 2010", h: "Robot • 2010" },
  // === 2012-2013 ===
  { y: 2012, t: "Kadal • 01-02-2012", te: "Kadali • 2012" },
  { y: 2013, t: "Maryan • 19-07-2013", te: "Mariyaan • 2015" },
  { y: 2013, t: "Ambikapathy • 2013", h: "Raanjhanaa • 21-06-2013" },
  // === 2014-2015 ===
  { y: 2014, t: "Kochadaiyaan • 23-05-2014", te: "Vikram Simha • 2014", h: "Kochadaiyaan • 2014", o: "Kochadaiyaan (Malayalam) • 20-02-2023" },
  { y: 2014, t: "Kaaviya Thalaivan • 28-11-2014", te: "Premalayam • 2016", h: "Pradhi Nayagan • 2015" },
  { y: 2014, t: "Lingaa • 12-12-2014", te: "Lingaa • 2014", h: "Lingaa • 2014" },
  { y: 2015, t: "I (the movie) • 14-01-2015", te: "I Manoharudu • 2014", h: "I (the movie) • 2015" },
  { y: 2015, t: "OK Kanmani • 17-04-2015", te: "OK Bangaram • 2015", h: "OK Jaanu • 13-01-2017", m: "Malayan Kunju • 22-07-2022" },
  // === 2016-2017 ===
  { y: 2016, t: "24 • 06-05-2016", te: "24 • 2016" },
  { y: 2016, t: "Achcham Yenbadhu Madamaiyada • 11-11-2016", te: "Saahasam Swasaga Saagipo • 2016" },
  { y: 2017, t: "Katru Veliyidai • 07-04-2017", te: "Cheliyaa • 2017" },
  { y: 2017, t: "Sachin – A Billion Dreams • 2017", te: "Sachin – A Billion Dreams • 2017", h: "Sachin – A Billion Dreams • 29-05-2017", m: "Sachin – A Billion Dreams • 2017", o: "Sachin – A Billion Dreams (Marathi) • 2017" },
  { y: 2017, t: "MOM • 2017", te: "MOM • 2017", h: "MOM • 07-07-2017", m: "MOM • 2017 (Malayalam)" },
  { y: 2017, t: "Mersal • 08-10-2017", te: "Adirindhi • 2017" },
  { y: 2017, t: "2.0 • 29-11-2017", te: "2.0 • 2017", h: "2.0 • 2017" },
  { y: 2017, h: "Partition: 1947 • 2017", note: "Viceroy's House (2017) English OST" },
  // === 2018-2019 ===
  { y: 2018, t: "Chekka Chivantha Vaanam • 27-09-2018", te: "Nawab • 2018" },
  { y: 2018, t: "Sarkar • 06-11-2018", te: "Sarkar • 2018" },
  { y: 2019, t: "Sarvam Thaala Mayam • 09-02-2019", te: "Sarvam Thaala Mayam • 2019" },
  { y: 2019, t: "Bigil • 25-10-2019", te: "Whistle • 2019", o: "Bigil (Kannada) • 2019" },
  { y: 2019, t: "Avengers – Endgame • 2019", te: "Avengers – Endgame • 2019", h: "Avengers – Endgame • 2019", note: "Indian language versions" },
  // === 2021-2022 ===
  { y: 2021, t: "99 Songs • 2021", te: "99 Songs • 2021", h: "99 Songs • 16-04-2021" },
  { y: 2021, t: "99 Songs online concert for JIO • 2021", te: "99 Songs online concert for JIO • 2021", h: "99 Songs online concert for JIO • 2021" },
  { y: 2021, t: "Song – Shirdi Sai • 2021", te: "Song – Shirdi Sai • 2021", h: "Song – Shirdi Sai • 2020", o: "Shirdi Sai (Kannada) • 2021" },
  { y: 2021, t: "Galatta Kalyanam • 2021", h: "Atrangi Re • 24-12-2021" },
  { y: 2022, t: "Cobra • 31-08-2022", te: "Cobra • 2022", h: "Cobra • 2022 (Hindi)", m: "Cobra • 2022 (Malayalam)", o: "Cobra (Kannada) • 2022" },
  { y: 2022, t: "Ponniyin Selvan Part 1 • 30-09-2022", te: "Ponniyin Selvan Part 1 • 2022", h: "Ponniyin Selvan Part 1 • 2022", m: "Ponniyin Selvan Part 1 • 2022", o: "Ponniyin Selvan Part 1 (Kannada) • 2022" },
  { y: 2022, t: "Vendhu Thanindhathu Kaadu • 15-09-2022", te: "Life of Muthu • 2022 (VTK-Telugu)", note: "Venthu Thanindhadu Kaadu • 12-02-2023" },
  // === 2023-2024 ===
  { y: 2023, t: "Ponniyin Selvan Part 2 • 28-04-2023", te: "Ponniyin Selvan Part 2 • 2023", h: "Ponniyin Selvan Part 2 • 2023", m: "Ponniyin Selvan Part 2 • 2023 (Malayalam)", o: "Ponniyin Selvan Part 2 (Kannada) • 2023" },
  { y: 2023, t: "Maamannan • 01-06-2023", te: "Nayakudu • 2023" },
  { y: 2023, t: "Pathu Thala • 18-03-2023", te: "AGR • 02-01-2024", h: "AGR • 02-01-2024" },
  { y: 2024, t: "Ayalaan • 10-01-2024", te: "Ayalaan • 10-12-2024" },
  { y: 2024, t: "Lal Salaam • 26-01-2024", te: "Lal Salaam • 15-02-2024", h: "Lal Salaam • 29-02-2024" },
  { y: 2024, t: "Aadujeevitham – The Goat Life • 18-03-2024", te: "Aadujeevitham – The Goat Life • 18-03-2024", h: "Aadujeevitham – The Goat Life • 18-03-2024", m: "Aadujeevitham – The Goat Life • 14-03-2024", o: "Aadujeevitham – The Goat Life (Kannada) • 18-03-2024" },
  { y: 2024, t: "Maidaan • 12-06-2024", te: "Maidaan • 12-06-2024", h: "Maidaan • 08-04-2024", m: "Maidaan • 12-06-2024", o: "Mudhalvan (Kannada) • 11-12-2023" },
  { y: 2024, t: "Raayan • 06-07-2024", te: "Raayan • 21-07-2024", h: "Raayan • 21-07-2024", m: "Raayan • 27-08-2024 (Malayalam)", o: "Kaathavaraayan (Kannada) • 27-08-2024" },
  // === 2025-2026 ===
  { y: 2025, t: "Kadhalikka Neramillai • 07-01-2025", te: "Kadhalikka Neramillai • 11-02-2025", h: "Kadhalikka Neramillai • 11-02-2025", m: "Kadhalikka Neramillai • 11-02-2025", o: "Kadhalikka Neramillai (Kannada) • 11-02-2025" },
  { y: 2025, t: "Chhaava • 12-02-2025", te: "Chhaava • 28-03-2025" },
  { y: 2025, t: "Thug Life • 24-05-2025", te: "Thug Life • 24-05-2025", h: "Thug Life • 24-05-2025" },
  { y: 2025, t: "Tere Ishk Mein • 02-12-2025", te: "Amara Kavyam • 02-12-2025", h: "Tere Ishk Mein • 12-11-2025" },
  { y: 2025, t: "Peddi (Music Launch)", te: "Peddi (Music Launch)", h: "Peddi (Music Launch)", m: "Peddi (Music Launch)", o: "Peddi (Music Launch) Kannada" },
  { y: 2026, t: "Gandhi Talks • 26-01-2026", te: "Gandhi Talks • 26-01-2026", h: "Gandhi Talks", m: "Gandhi Talks • 26-01-2026", o: "Gandhi Talks (Marathi) • 26-01-2026" },
  // === Padaiyappa Kannada late dub ===
  { y: 1999, o: "Padaiyappa (Kannada) • 09-12-2025", note: "Kannada dub" },
];

// ============================================================================
// UNDUBBED FILM LISTS
// ============================================================================

const TAMIL_UNDUBBED = [
  { title: "Uzhavan", date: "13-11-1993", year: 1993 },
  { title: "Pavithra", date: "02-11-1994", year: 1994 },
  { title: "Puthiya Mannargal", date: "02-12-1994", year: 1994 },
  { title: "Anthi Mandhaaarai", date: "01-06-1996", year: 1996 },
  { title: "Sangamam", date: "16-07-1999", year: 1999 },
  { title: "Taj Mahal", date: "07-11-1999", year: 1999 },
  { title: "Alli Arjuna", date: "14-01-2002", year: 2002 },
  { title: "Kaadhal Virus", date: "20-11-2002", year: 2002 },
  { title: "Udhaya", date: "26-04-2004", year: 2004 },
  { title: "Kangalal Kaidhu Sei", date: "20-02-2004", year: 2004 },
  { title: "Ah Aah / Anbe Aaruyire", date: "09-09-2005", year: 2005 },
  { title: "Sakkarakatti", date: "26-09-2008", year: 2008 },
  { title: "Iravin Nizhal", date: "15-07-2022", year: 2022 },
  { title: "Genie (Single)", date: "07-10-2025", year: 2025 },
  { title: "MoonWalk", date: "12-01-2026", year: 2026 },
];

const TELUGU_UNDUBBED = [
  { title: "Komaram Puli", date: "10-09-2010", year: 2010 },
];

const HINDI_UNDUBBED = [
  { title: "Fire", date: "05-11-1998", year: 1998 },
  { title: "1947 Earth", date: "10-09-1999", year: 1999 },
  { title: "Thakshak", date: "03-12-1999", year: 1999 },
  { title: "Pukar", date: "04-02-2000", year: 2000 },
  { title: "Fiza", date: "08-09-2000", year: 2000 },
  { title: "Zubeidaa", date: "19-01-2001", year: 2001 },
  { title: "One 2 Ka 4", date: "30-03-2001", year: 2001 },
  { title: "Lagaan", date: "15-06-2001", year: 2001 },
  { title: "The Legend Of Bhagath Singh", date: "07-06-2002", year: 2002 },
  { title: "Nayak", date: "2001", year: 2001 },
  { title: "Tehzeeb", date: "21-11-2003", year: 2003 },
  { title: "Dil Ne Jise Apna Kaha", date: "10-09-2004", year: 2004 },
  { title: "Lakeer", date: "14-05-2004", year: 2004 },
  { title: "Meenaxi: A Tale Of 3 Cities", date: "02-04-2004", year: 2004 },
  { title: "Bose: The Forgotten Hero", date: "13-05-2005", year: 2005 },
  { title: "Mangal Pandey: The Rising", date: "12-08-2005", year: 2005 },
  { title: "Water", date: "09-09-2005", year: 2005 },
  { title: "Rang De Basanti", date: "27-01-2006", year: 2006 },
  { title: "Ada", date: "31-12-2010", year: 2010 },
  { title: "Ghajini", date: "25-12-2008", year: 2008 },
  { title: "Jaane Tu Ya Jaane Naa", date: "04-07-2008", year: 2008 },
  { title: "Yuvvraaj", date: "21-11-2008", year: 2008 },
  { title: "Delhi 6", date: "20-02-2009", year: 2009 },
  { title: "Jhoota Hi Sahi", date: "22-10-2010", year: 2010 },
  { title: "Rockstar", date: "11-11-2011", year: 2011 },
  { title: "Jab Tak Hai Jaan", date: "13-11-2012", year: 2012 },
  { title: "Highway", date: "21-02-2014", year: 2014 },
  { title: "Lekar Hum Deewana Dil", date: "04-07-2014", year: 2014 },
  { title: "Tamasha", date: "27-11-2015", year: 2015 },
  { title: "Mohenjodaro", date: "12-08-2016", year: 2016 },
  { title: "Sanju", date: "29-06-2018", year: 2018, note: "2 tracks" },
  { title: "Love Sonia", date: "06-09-2019", year: 2019, note: "1 track" },
  { title: "The Fakir Of Venice", date: "08-12-2019", year: 2019 },
  { title: "Dil Bechara", date: "24-07-2020", year: 2020 },
  { title: "Mimi", date: "26-07-2021", year: 2021 },
  { title: "Heropanti 2", date: "29-04-2022", year: 2022 },
  { title: "Mili", date: "04-11-2022", year: 2022 },
  { title: "Gandhi Vs Godse – Ek Yudh", date: "26-01-2023", year: 2023 },
  { title: "Pippa", date: "07-11-2023", year: 2023 },
  { title: "Amar Singh Chamkila", date: "26-03-2024", year: 2024 },
  { title: "Ramayana (Introduction)", date: "04-07-2025", year: 2025 },
  { title: "Uff Yeh Siyapaa", date: "12-09-2025", year: 2025 },
  { title: "Main Vapas Aaunga", note: "Singles released" },
];

const MALAYALAM_UNDUBBED = [
  { title: "Malayan Kunju", date: "22-07-2022", year: 2022 },
];

// ============================================================================
// FOREIGN LANGUAGES & OTHER (Section 5)
// ============================================================================

const FOREIGN_OST = [
  { title: "Fire", year: 1996, note: "OST" },
  { title: "Earth", year: 1998, note: "OST" },
  { title: "Warriors of Heaven & Earth", date: "16-10-2004", year: 2004 },
  { title: "Water", year: 2006, note: "OST" },
  { title: "Elizabeth — The Golden Age", date: "12-10-2007", year: 2007 },
  { title: "Bombil and Betrice", year: 2007 },
  { title: "Couples Retreat", date: "09-10-2009", year: 2009 },
  { title: "127 Hours", date: "02-11-2010", year: 2010 },
  { title: "People Like Us", date: "29-06-2012", year: 2012 },
  { title: "Million Dollar Arm", date: "16-05-2014", year: 2014 },
  { title: "The Hundred-Foot Journey", date: "08-08-2014", year: 2014 },
  { title: "Pele: Birth of a Legend", date: "06-05-2016", year: 2016 },
  { title: "Viceroy's House", date: "18-08-2017", year: 2017 },
  { title: "Beyond The Clouds", date: "20-04-2018", year: 2018 },
  { title: "Blinded By The Light", date: "09-08-2019", year: 2019 },
  { title: "Tell it Like a Woman", year: 2022 },
  { title: "Le Musk", date: "21-08-2024", year: 2024 },
];

const CHINESE_FILMS = [
  { title: "Tian Di Ying Xiang", year: 2003, note: "Chinese" },
];

const PERSIAN_ARABIC = [
  { title: "Muhammed: Messenger of God", date: "12-02-2015", year: 2015 },
];

const URDU_FILMS = [
  { title: "Al-Risalah", year: 2008 },
];

// ============================================================================
// FILM INSTRUMENTALS, BGM/SCORE/OST
// ============================================================================

const FILM_INSTRUMENTALS = [
  { title: "Roja [Tamil, 1992]", year: 1992 },
  { title: "Roja [Telugu, 1992]", year: 1992 },
  { title: "Roja [Hindi, 1994]", year: 1994 },
  { title: "Gentleman [Tamil, 1993]", year: 1993 },
  { title: "Gentleman [Telugu, 1993]", year: 1993 },
  { title: "May Madham [Tamil, 1994]", year: 1994 },
];

const BGM_SCORE = [
  { title: "Endhiran", date: "28-11-2018", year: 2018 },
  { title: "2.0", date: "29-06-2019", year: 2019 },
  { title: "Shikara", date: "07-02-2020", year: 2020 },
  { title: "99 Songs", date: "23-12-2022", year: 2022 },
  { title: "Vendhu Thanindhathu Kaadu", date: "12-02-2023", year: 2023 },
  { title: "Ponniyin Selvan", date: "06-01-2024", year: 2024 },
  { title: "The Goat Life", date: "12-04-2024", year: 2024 },
  { title: "Kadhalikka Neramillai" },
  { title: "Aayalan (Score)", note: "Announced" },
  { title: "Gandhi Talks Score" },
];

// ============================================================================
// FORTHCOMING, ANNOUNCED, IN PROGRESS
// ============================================================================

const FORTHCOMING = [
  { title: "Can I Go Home Now? (English Documentary)" },
  { title: "Dilkashi", note: "Lijo Jose Pellissery / Hansal Mehta" },
  { title: "BAAB", note: "UAE — Nayla Al Khaja" },
  { title: "Lahore 1947" },
  { title: "Gandhi — Web Series", note: "Hansal Mehta" },
  { title: "Ramayana 1", note: "Nitesh Tiwari + Hans Zimmer · 2026" },
  { title: "Ramayana 2", note: "Nitesh Tiwari + Hans Zimmer · 2027" },
  { title: "KHOJ", note: "Previously Mahasangam / Bharat Bala" },
  { title: "Killer", note: "SJ Suriya" },
  { title: "No Land's Man" },
  { title: "Mari Selvaraj + Dhanush + Ishari Ganesh Film" },
  { title: "Mani Rathnam + Vijay Sethupathi + Sai Pallavi Film" },
  { title: "Kamal aur Meena", note: "Siddharth Malhotra · 2025" },
];

const ANNOUNCED_PROJECTS = [
  { title: "Bhanushali Studios Project", note: "Dir. Anthony D'Souza" },
  { title: "One World One Family Mission Anthem" },
  { title: "Imaginary Rain" },
  { title: "SSGH Mission Hospital Healing Music Project" },
  { title: "Dhruv 4", note: "Ramesh Varma untitled film" },
  { title: "Rumi", note: "Arno Krimmer" },
];

const NO_UPDATES = [
  { title: "WhatsApp DP", note: "Kathir" },
  { title: "Confessions", note: "VR film" },
  { title: "Hands Around the World", note: "Announced" },
  { title: "Sahara Sri — Subrata Roy Biopic" },
  { title: "Slumdog Millionaire [Sequel]" },
  { title: "Slumdog Millionaire [Musical]" },
  { title: "Slumdog Millionaire [TV Series]" },
  { title: "Elevate", note: "Nexa Music Album" },
  { title: "Mulla Nasruddin [Musical]" },
  { title: "Sharing a Ride", note: "Leena Yadav" },
  { title: "Zuni", note: "Santosh Sivan" },
  { title: "Ebony McQueen", note: "Shekar Kapur" },
];
