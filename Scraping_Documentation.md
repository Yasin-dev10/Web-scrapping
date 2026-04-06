# Warqad Sharaxaad ah: Habka ay u Shaqeyso Web Scrapping-ka (Facebook & News)

Document-kan wuxuu faahfaahin ka bixinayaa sida barnaamijkan u shaqeeyo, agabka (tools) la isticmaalay, iyo nidaamka guud ee xogta looga soo ururiyo bogagga internet-ka, gaar ahaan Facebook iyo mareegaha wararka.

---

## 1. Waa maxay Web Scraping?
Web scraping waa farsamo lagu soo ururiyo xog aad u tiro badan oo ku jirta bogagga internet-ka iyadoo loo rogayo qaab habaysan (sida CSV ama Excel). Halkii aad gacantaada ku koobiyeyn lahayd (copy-paste), barnaamijkan ayaa si toos ah u sameynaya shaqadaas.

---

## 2. Agabka la Isticmaalay (Technologies & Libraries)
Barnaamijkan waxaa lagu dhisay luuqadda **Python**, waxaana loo adeegsaday maktabadaha (libraries) soo socda:

*   **Selenium**: Waxaa loo isticmaalaa in lagu maamulo browser-ka (Chrome). Waxay ka dhigtaa barnaamijka mid u dhaqmaya sidii qof bani'aadam ah oo kale, isagoo furaya bogga, gujinaya badhamada, oo qoraya ereyada raadiska (keywords).
*   **BeautifulSoup4**: Waxaa loo adeegsadaa in lagu dhex baaro HTML-ka bogga si looga dhex saaro qoraallada, xiriiriyeyaasha (links), iyo taariikhaha muhiimka ah.
*   **Pandas**: Waa maktabad loo isticmaalo maaraynta iyo habaynta xogta (Data Processing). Waxay u sahlaysaa barnaamijka inuu xogta ku keydiyo qaab CSV ah oo nadiif ah.
*   **WebDriver Manager**: Wuxuu si toos ah u soo dejiyaa darawalada (drivers) loogu baahan yahay in barnaamijka uu ku maamulo Chrome.

---

## 3. Sida uu u Shaqeynayo (How it Works)
Habka shaqada ee barnaamijkan wuxuu maraa dhowr marxaladood oo muhiim ah:

### A. Furitaanka Browser-ka & Galitaanka (Login)
Barnaamijku wuxuu marka hore furaa daaqad Chrome ah oo cusub. Marka la rabo in xog looga soo saaro Facebook, barnaamijku wuxuu xasuusanayaa **Cookies-ka** (xogta galitaanka) haddii hore loo galiyay, haddii kalena wuxuu ku siinayaa fursad aad gacantaada ku gasho (Manual Login) si looga fogaado amniga Facebook.

### B. Raadinta Xogta (Searching)
Marka barnaamijku uu galo Facebook ama bogagga kale, wuxuu isticmaalaa **Keywords** (ereyo lala socdo) oo aad adigu cayintay. Wuxuu dhex maraa natiijooyinka raadiska, isagoo kor iyo hoos u soconaya (**Scrolling**) si uu u soo saaro dhammaan qoraallada (posts) jira.

### C. Soo Saarista Xogta (Extraction)
Barnaamijku wuxuu "aqrinayaa" mareegta, isagoo kala saaraya:
*   Qoraalka qoraalka (Post Content).
*   Magaca qofka ama bogga qoraalka soo dhigay.
*   Waqtiga la soo dhigay.
*   Link-ga tooska ah ee qoraalkaas.

### D. Keydinta Xogta (Storage)
Marka xogta la ururiyo, waxaa loo beddelaa qaab **CSV** ah. Faylkaas waxaa loogu magac darayaa waqtiga la ururiyay si aysan xogtu isku dhex darsamin.

---

## 4. Nadiifinta iyo Kala Shaandheynta (Cleanup & Filtering)
Barnaamijku ma ururiyo oo keliya xogta, ee wuxuu kaloo leeyahay awood uu ku kala shaandheeyo. Tusaale ahaan:
*   **Filter Crime**: Waxaa loo adeegsan karaa in laga dhex raadiyo oo keliya qoraallada la xiriira dembiyada (crime-related), isagoo meesha ka saaraya qoraallada aan muhiimka ahayn.
*   **Cleanup CSV**: Waxaa jira script-yo (sida `cleanup_csv.py`) oo tirtira safafka iyo tiirarka (rows/columns) aan loo baahnayn si xogta u noqoto mid tayo leh.

---

## 5. Ka Hortagga Xannibaadda (Anti-Ban)
Maadaama Facebook uu adag yahay, barnaamijkan wuxuu isticmaalaa farsamooyin looga hortagayo in la xannibo (Ban):
*   Wuxuu ku darayaa **Waxti Sugitaan (Sleep/Wait)** inta u dhaxaysa shaqooyinka si uusan u dhaqmin sidii Robot aad u ordaysan.
*   Wuxuu isticmaalaa fadhiga isticmaalaha (User Session) si uusan mar kasta ugu baahnaan login cusub.

---

## Gabagabo
Barnaamijkan waa qalab xooggan oo kuu sahlaya inaad xog aad u badan ku ururiso waqti yar, adigoon u baahneyn inaad adigu gacantaada mid-mid ugu raadiso. Waxaad si joogto ah ugu isticmaali kartaa inaad kula socoto wararka ama qoraallada laga qoro mowduucyada aad xiisaynayso.
