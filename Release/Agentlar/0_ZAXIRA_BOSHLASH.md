# Shaxsiy zaxira 0.1 • Android va Telegram

Telefon yo‘qolsa yoki o‘chsa, oldin zaxiralangan hujjatni shaxsiy Telegram botingizdan olasiz. Bu bir egali sinovda ombor Windows kompyuteringizda turadi. Kompyuter va bot internetga ulangan holda ishlashi kerak. Telefon faqat yangi hujjatni zaxiralash vaqtida kerak. Qidiruv fayl nomi bo‘yicha ishlaydi. Avvalgi loyiha buyruqlari ham mavjud.

## Birinchi ishga tushirish

1. Ishlab turgan eski Agentlar botini uning oynasida Ctrl+C bilan to‘xtating. Agentlar papkangizning zaxira nusxasini oling.
2. ZIPni alohida joyga chiqaring. Ichidagi **Agentlar** papkasini oching. Uning **ichidagi fayl va papkalarni** eski botning `config.json` joylashgan papkasiga nusxalang. Bir xil dastur fayllarini yangilang. Paketda shaxsiy `config.json`, avvalgi vazifalar yoki foydalanuvchi fayllari yo‘q. Natijada `config.json` va `8_ZAXIRA_START.bat` bir papkada bo‘ladi.
3. **8_ZAXIRA_START.bat** ni oching. Birinchi marta alohida Python muhiti yaratilib, shifrlash kutubxonasi PyPI’dan o‘rnatiladi. Oynada “Zaxira tayyor” chiqadi. Oynani ochiq qoldiring.
4. **9_ZAXIRA_INTERNET.bat** ni oching. Agar Cloudflared topilmasa, PowerShell’da `winget install --id Cloudflare.cloudflared -e` buyrug‘ini bajaring. Yangi terminaldan 9-faylni qayta oching. Oynada chiqqan `https://...trycloudflare.com` manzilini oling. Yangi yuklashlar uchun shu oyna ham ochiq turadi. Routerga port ochish shart emas.
5. **Shaxsiy_Zaxira_0_1.apk** ni Android telefonga o‘rnating. Ilova alohida nom bilan ko‘rinadi. Telegramdagi shaxsiy botingizga **/zpair** yuboring. Ilovaga aynan 9-oynadagi HTTPS manzilini va bot bergan kodni kiriting, **Biriktirish** tugmasini bosing. Kod 5 daqiqa, bitta muvaffaqiyatli ulanish uchun amal qiladi.
6. **Hujjat tanlash va zaxiralash** tugmasini bosib kichik PDF yoki boshqa hujjat tanlang. Ilovada server tasdig‘i, nomi va Telegramdan olish buyrug‘i ko‘ringuncha kuting. Bir fayl 10 MiB gacha. Nomi va tarkibi bir xil nusxa qayta yuklansa joy takror band bo‘lmaydi. O‘zgargan tarkib uchun alohida nusxa saqlanadi.

## Telefon o‘chiq bo‘lgandagi sinov

Masalan, `Diplom.pdf` nomli faylni saqlang. Tasdiq chiqqach, telefonni o‘chiring yoki aviarejimga o‘tkazing. Kompyuterda internet va 8-oyna ishlashda davom etsin. Oldindan kirilgan Telegram Desktop’dan ayni botga **Diplomimni top** deb yozing. Bot topilgan fayl nomi, hajmi, saqlangan vaqti va `/zol_...` buyrug‘ini ko‘rsatadi. Shu buyruqni bossangiz, bot fayl nusxasini faqat bog‘langan shaxsiy chattingizga yuboradi. Yuklab oling va ochib tekshiring. 9-oyna yopilgan bo‘lsa ham avvalgi zaxiradan olish mumkin.

| Telegram buyrug‘i | Vazifasi |
| --- | --- |
| /zaxira yoki Hujjatimni top | Eng so‘nggi 10 nusxa |
| /zfind diplom yoki Diplomimni top | Nomiga mos oxirgi 10 nusxa |
| /zol_ID | Tanlangan nusxaning o‘zini yuborish |
| /zpair | Yangi juftlash kodi |
| /zoff | Telefonning serverga yozish ruxsatini bekor qilish |
| /zhelp | Buyruqlar |

## Saqlash va qayta ulash

- Server fayl baytlari va nomlarini AES-256-GCM bilan shifrlaydi. Ombor `private_backup/vault.sqlite3`, kalit `private_backup/vault.key`. Fayl hajmi va saqlash vaqti ochiq metadata. Server parol menejeri hisoblanmaydi. Kalit va ombor o‘qish huquqi bo‘lgan mahalliy foydalanuvchi nusxalarni ochishi mumkin.
- Kompyuter diski ishdan chiqishidan himoyalanish uchun botni to‘xtatib, butun `private_backup` papkasini ishonchli shifrlangan tashqi diskka nusxalang. Uni Telegramga yubormang va Git’ga yuklamang. Tiklash uchun papkani joyiga qo‘ying va avvalgi Telegram egasi hisobi bilan 8-faylni oching. Kalit yo‘qolsa, zaxira ochilmaydi.
- Butun ombor bir egaga 512 MiB va 1000 nusxagacha. 10 tadan oldingi faylni aniqroq nomi yoki ilova ko‘rsatgan ID bilan oling. Fayl ichidagi matn yoki rasm mazmuni bo‘yicha qidiruv bu sinovga kirmaydi.
- Bot qayta ishga tushganda telefonni yana biriktiring: ilovada **Ulanishni uzish**, Telegramda **/zpair**. Tunnel qayta ochilganda yangi manzilni ishlating. Allaqachon saqlangan fayllarni olish uchun qayta juftlash shart emas.
- 8-faylni ishlatayotganda 2-faylni parallel ochmang. Oddiy agent rejimiga qaytish uchun 8-oynani Ctrl+C bilan yopib, 2-faylni oching.
- Telefon faqat foydalanuvchi tizim oynasidan tanlagan faylni yuboradi. Yuborish HTTPS tunnel orqali kompyuterga boradi. Tiklash buyrug‘i berilganda nusxa Telegram xabarida ham saqlanadi. Ushbu mahalliy zaxira funksiyasi Gemini API ishlatmaydi.
- Pullik hosting, iOS, SMS/Google bilan yangi hisob va telefonsiz login, kontaktlarni avtomatik sinxronlash, lokatsiya keyingi bosqichlar uchun. APK pilot tarqatish uchun imzolangan. Asl Samsung va jonli Telegram bilan yakuniy sinov egasining qurilmasida bajariladi.

## Dasturchi uchun

Yangi kod `zaxira/store.py`, `receiver.py`, `bot.py`, Android manbasi `zaxira/mobile` ichida. Python 3.11+ va `zaxira-requirements.txt` zarur. Tekshirish uchun `python -m unittest discover -s tests`. Android manbani qayta yig‘ish uchun JDK, SDK Platform 30, Build Tools 34.0.0 bilan `python zaxira/mobile/build_android.py --sdk SDK_YOLI` ishlating. O‘zingizning doimiy imzolash kalitingizdan foydalaning. Mahalliy kalit bilan qayta yig‘ilgan APKni o‘rnatish uchun ushbu sinov APKsini telefondan o‘chirish talab qilinishi mumkin; serverdagi nusxalar saqlanadi.
