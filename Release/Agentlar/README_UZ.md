# Shaxsiy zaxira sinovi

Yangilash va sinov uchun **0_ZAXIRA_BOSHLASH.md** ni oching.

# Yangi: 1.3 — PC va Android11 fayllari

Boshlash: **TELEFON_PC_QOLLANMA.md**. Tayyor APK: **Agentlar_Telefon_1_3.apk**.

# AGENTLAR TELEGRAM V1.2.1 — KOMPYUTERDA DASTUR YIG‘ISH

Telegramga topshiriq yozasiz; Windows kompyuteringizdagi agent reja, kod, lokal build va tekshiruvlarni bajaradi, natija ZIPini yuboradi. Gemini API bulutda ishlaydi; bu versiya RTX 5070 GPUda mahalliy model ishlatmaydi.

## Mavjud V1/V1.1 dan yangilash

1. Eski bot oynasida Ctrl+C bosing, yopilishi tugashini kuting.
2. ZIPdagi `Agentlar_Telegram_v1` papkasi ichidagi fayllarni eski papka ichiga ko‘chiring va bir xil nomlilarini almashtiring.
3. `config.json`, `state`, `projects`, `exports` ni O‘CHIRMANG. ZIPda haqiqiy kalitlar yo‘q.
4. `4_LOCAL_BUILD_SOZLASH.bat` ni oching. U Python, Node/npm va WSL mavjudligini ko‘rsatadi. Local buildni yoqishga `HA` deb javob bering.
5. `2_ISHGA_TUSHIRISH.bat` ni oching. Telegramga `/doctor` yuboring.
6. Yangi topshiriq yozing yoki `/resume ID` bilan oldingi xatolangan ishni davom ettiring.

Qaytadan bot tokeni va Gemini kaliti kiritish shart emas. `4_LOCAL_BUILD_SOZLASH.bat` mavjud sozlamalarga uchta parametr qo‘shadi, model va kalitlarni saqlaydi. `config.before-local-build.json` zaxirasida ham kalitlar bor — uni tarqatmang.

## Birinchi marta o‘rnatish

- Python 3.11+ kerak: https://www.python.org/downloads/windows/ . Add python.exe to PATH ni belgilang.
- Web loyihalar uchun Node.js LTS: https://nodejs.org/en/download . O‘rnatgandan keyin terminalni qayta oching.
- `1_SOZLASH.bat` → Telegram BotFather tokeni, Gemini API kaliti, mavjud modelni tanlash, hisobni /pair bilan biriktirish.
- `4_LOCAL_BUILD_SOZLASH.bat` → local buildni yoqish.
- `2_ISHGA_TUSHIRISH.bat` → agentni ishga tushirish.
- `0_TEKSHIRISH.bat` → offline testlar. Node testi Node/npm bo‘lsa ishlaydi.

Gemini kaliti: https://aistudio.google.com/apikey . Telegram bot: https://t.me/BotFather . Kalitlarni chatga yubormang.

## Birinchi sinov topshirig‘i

> Menga Python dastur yarat: xarajat nomi, summasi va sanasini SQLite bazaga saqlasin. Xarajat qo‘shish, ro‘yxat ko‘rish va jami hisoblash CLI buyruqlari bo‘lsin. tests/test_*.py funksional testlarini yoz, python build profili bilan kompyuterimda tekshir, ishga tushirish yo‘riqnomasi bilan tayyor ZIPni yubor.

Web sinov:

> Menga Vite asosida o‘zbekcha portfolio sayt yarat. package.json da bir marta bajarilib tugaydigan test va build skriptlari bo‘lsin. Testlarni bajar, dist papkasiga build qil, manba va tayyor distni ZIP qilib yubor.

## Build profillari

| Profil | Haqiqiy bajariladigan ish | Yetkaziladigan natija |
|---|---|---|
| python | Har urinishda yangi .venv, requirements.txt bo‘lsa pip install, unittest discover; 0 test muvaffaqiyat hisoblanmaydi | Tekshirilgan manba ZIPi va BUILD_REPORT.json; EXE emas |
| web | npm install/ci, npm run test, eski distni tozalash, npm run build, yangi dist mavjudligini tekshirish | source/ va dist/ joylashgan ZIP |
| static | index.html mavjudligi, manbani paketlash | HTML/CSS/JS ZIP; brauzer testi bajarilmagan deb ochiq belgilanadi |

Web profil hozir `dist/` chiqishini talab qiladi. Next.js .next, Android APK, Windows EXE, Docker va WSL ichida build qilish bu versiyaga kirmaydi. WSL faqat aniqlanadi; mavjud Ubuntu o‘zgartirilmaydi. Murakkab loyihalarda agentning yozgan testlari barcha xatolarni qamrab olmasligi mumkin.

Bir ishga tushirishda 3 ta build urinish; har build jami 20 daqiqagacha, alohida install 10 daqiqagacha. Dastur xatoni agentga qaytaradi; urinish limiti tugasa /resume bilan davom etasiz. Uzoq ishlaydigan server build tugagach qoldirilmaydi. Natijani lokal ishga tushirish ko‘rsatmasi loyihaning README faylida bo‘lishi kerak.

## Local build ruxsati

`allow_local_build: true` yoqilgach, yaratilgan Python/Node kodi, bog‘liqliklar, install skriptlari va testlar Windows foydalanuvchingiz huquqida ishlaydi. **Bu sandbox emas: kod boshqa papkalarga va tarmoqqa kira oladi.** Loyiha papkasini alohida qilish OS xavfsizlik izolatsiyasi emas. Virtual mashina yoki alohida Windows hisobidan foydalanish xavfni kamaytiradi. Agentga faqat o‘zingiz tushungan topshiriqlarni yuboring.

Erkin `command` amali alohida: `allow_commands` standart false. Uni yoqsangiz ham aniq buyruq Telegramdagi /approve ID KOD bilan tasdiqlanadi. Local build ruxsati erkin shell buyruqlariga ruxsat bermaydi, ammo loyiha test/build skriptlari baribir kod bajaradi.

## Natijani tasdiqlash

Software fayllari bo‘lsa local build yoqilmaguncha vazifa `needs_setup` bo‘ladi. Build va AI ko‘rigidan keyin manba hamda ZIPning SHA-256 qiymatlari qayta tekshiriladi. Eski yoki o‘zgargan ZIP bilan `done` berilmaydi. npm lockfile manba ZIPi va xeshga kiradi, lekin katta bo‘lishi mumkinligi uchun model ko‘rigiga avtomatik qo‘shilmaydi.

ZIP avtomatik yuboriladi. Telegram uzilib qolsa diskdagi natija saqlanadi; `/files ID` bilan qayta yuboring. 15 MiB dan katta ZIP bu versiyada avtomatik jo‘natilmaydi. Loyihalar `projects/ID/`, arxivlar `exports/`, holatlar `state/` ichida.

## Jarayon va buyruqlar

- `/status` — oxirgi ishlar, bosqich va qadam.
- `/doctor` — Python/Node/npm/WSL, model va local build holati.
- `/stop` — ishni to‘xtatish. Joriy API javobi kelguncha kutish mumkin.
- `/resume ID` — uzilgan/xatolangan ishni davom ettirish.
- `/change ID yangi talab` — mavjud loyihani o‘zgartirish va qayta tekshirish.
- `/files ID` — natijani qayta olish.
- `/search savol` — Google Search grounding bilan manbali Markdown hujjat.
- `/sources` — ruxsat etilgan o‘qish papkalari.

AI so‘rovi cho‘zilsa 45 soniyada, build cho‘zilsa 30 soniyada holat xabari keladi. Bu aniq bajarilgan foiz emas. Telegramda bo‘lmasangiz ham kompyuter ishlayotgan bo‘lsa ish davom etadi. `keep_awake: true` Windowsning avtomatik uyqusini agent ishlayotganda to‘xtatishga urinadi; ekran o‘chishi mumkin. Qo‘lda Sleep/Shutdown, elektr uzilishi yoki internet yo‘qligini chetlab o‘tmaydi. Windows bilan avtomatik start hali qo‘shilmagan.

## Gemini limitlari

Standart `gemini_min_interval: 15` — ushbu jarayondan API urinishlari orasida kamida 15 soniya. 429 bo‘lsa Retry-After/RetryInfo hisobga olinadi; kunlik kvota deb qaytsa tez-tez urinish to‘xtatiladi. 15 soniyalik interval kunlik kvota yoki boshqa ilovalarning shu loyihadagi so‘rovlarini bartaraf etmaydi. Limitlarni https://aistudio.google.com/rate-limit da tekshiring.

JSON uchun aniq sxema va native function calling NONE ishlatiladi. Noto‘g‘ri function-call javobida bir marta qayta urinish bor. Google Search boshqa so‘rovda ishlaydi; manba metadata yo‘q bo‘lsa internetdan tekshirilgan deb belgilanmaydi. Model/hisob qidiruvni qo‘llashi va kvotasi bo‘lishi kerak.

## Hali qo‘shilmagan imkoniyatlar

Samsung A30s bilan fayl almashish, Android boshqaruvi, Word/PDF/Excel tahriri, tayyor PDF renderi, ovozli xabar, ommaviy hosting va APK/EXE yig‘ish yo‘q. Telegramga vazifani matn qilib yuboring. Tanlangan shaxsiy papkalardagi UTF-8 matnlarni o‘qish bor; ular Gemini ga yuborilishi mumkin. Asl shaxsiy fayl ustiga avtomatik yozilmaydi. Maxfiy kalitlar va hujjatlarni manba papkasiga qo‘ymang.

## Tekshirilgan holat

45 offline test, Python unittest bilan real kod, Node npm/test/build bilan real loyiha, stale dist, buzilgan ZIP, eskirgan manba, bekor qilish va kvota holatlari Linuxda tekshirildi. Haqiqiy Windows Job Object, foydalanuvchining Telegram/Gemini ulanishi va mahalliy Node o‘rnatmasi bu muhitda sinovdan o‘tkazilmagan. Birinchi qurilma sinovi /doctor va yuqoridagi kichik topshiriq bilan bajariladi.


## V1.2.1 tuzatishi
V1.2.1 — UTF-8 / SQLite tuzatishi

1. Botning kompyuterdagi oynasini Ctrl+C bilan to‘xtating, yopilishini kuting.
2. ZIPdagi Agentlar_Telegram_v1 ichidagi fayllarni eski shu papka ichiga ko‘chiring, bir xil nomlilarini almashtiring.
3. config.json, state, projects, exports ni O‘CHIRMANG.
4. 2_ISHGA_TUSHIRISH.bat ni qayta oching. Qayta sozlash kerak emas.
5. Telegramga yuboring:
/resume job_20261117_113816_dd63f4

Tuzatish: yakuniy AI ko‘rigida SQLite, rasm, PDF va boshqa ikkilik fayllar matn sifatida dekodlanmaydi. Ularning borligi va hajmi qayd etiladi; matn sifatida tekshirilmaganligi ko‘rsatiladi. Fayl baytlari va arxivga kiritilishi saqlanadi. Noto‘g‘ri kodlangan manba kodi jim e’tiborsiz qoldirilmaydi.
49 offline test PASS, jumladan haqiqiy SQLite bilan yakuniy ko‘rik va ZIPdagi baytlar saqlanishi.
Foydalanuvchining aynan shu loyihasi hali bu muhitga yuklanmagan; jonli Windowsdagi natijani /resume bilan tekshirish kerak.
