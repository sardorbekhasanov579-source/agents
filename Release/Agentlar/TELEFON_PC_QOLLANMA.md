# Agentlar 1.3 — Windows + Samsung A30s (Android 11)

## Ishlaydigan imkoniyatlar
Telegramdan tanlangan kompyuter papkasida fayl nomini qidirish, faylni olish, UTF-8 matnni o‘qish/tahrirlash. Tahrir avval ko‘rsatiladi; `/pcapply KOD` dan so‘ng zaxira bilan saqlanadi. Word/PDF fayllarni olish mumkin, ularning ichki mazmunini bu modul o‘zi tahrirlamaydi. Shaxsiy fayllar Gemini modeliga avtomatik uzatilmaydi.
Telefon ilovasi: tanlangan papkada fayl qidirish/olish, kompyuterdan shu papkaga yangi nusxa yuborish, batareya va oxirgi aloqa vaqti. Telefon ekranidagi tugmalarni bosish, boshqa ilovalarni boshqarish, kontakt/xabar/parollarni o‘qish yo‘q. Hozir qurilma amallari quyidagi aniq buyruqlar bilan ishlaydi; erkin matnli AI topshiriqlari avvalgidek loyiha yaratadi.

## 1. Botni yangilash
1. Eski bot oynasida Ctrl+C; yopilishini kuting.
2. ZIPni oching. Ichidagi `Agentlar_Telegram_v1` fayllarini eski Agentlar papkasiga nusxalang, bir xil kod fayllarini almashtiring. **config.json, state, projects, exports ni o‘chirmang.** Paketda shaxsiy sozlamalar yo‘q.
3. `5_PC_PAPKA_SOZLASH.bat` ni oching. Alohida hujjatlar papkasini tanlang; nomini `hujjat` deb kiriting. Qo‘shimcha papkalar uchun takrorlang. Diskning o‘zi/profil/Agentlar dastur papkasini tanlamang.
4. `6_TELEFON_SOZLASH.bat` ni oching.
5. `2_ISHGA_TUSHIRISH.bat` ni oching. Bu oyna ochiq tursin.

## 2. Kompyuterga Internet manzili
PowerShell da bir marta:
```
winget install --id Cloudflare.cloudflared -e
```
O‘rnatilgach terminalni yoping va `7_TELEFON_INTERNET.bat` ni oching. `https://....trycloudflare.com` havolasini toping. Shu oynani ham ochiq qoldiring. Agar cloudflared topilmasa Windows terminalini qayta oching yoki kompyuterdan chiqib qayta kiring.
Cloudflare Quick Tunnel sinov ulanishidir: har qayta ochilganda manzil o‘zgaradi, doimiy ishlash kafolati yo‘q. Barqaror manzil uchun keyingi bosqichda named tunnel kerak. Faqat loopback 8765 relay ochiladi; kompyuter kataloglari HTTP orqali e’lon qilinmaydi. Router portini ochish kerak emas.

## 3. Samsung A30s ni ulash
1. ZIPdagi `Agentlar_Telefon_1_3.apk` ni telefoningizga yuboring va o‘rnating. So‘ralsa aynan o‘rnatayotgan ilovaga APK o‘rnatish ruxsatini bering.
2. Telefon fayl menejerida masalan `Documents/Agentlar` papkasini yarating, kerakli fayllarni qo‘ying.
3. **Agentlar Telefon** ilovasini oching. Yuqoriga tunnel HTTPS manzilini kiriting.
4. **1. Papka tanlash** → `Documents/Agentlar` → foydalanishga ruxsat. Android11 butun disk, Download ildizi va Android/data kabi papkalarni tanlashni cheklaydi; alohida papka tanlang.
5. Telegram botingizga `/phonepair` yuboring; qaytgan kodni ilovaga kiriting. Kod 5 daqiqa va bir marta amal qiladi.
6. **2. Kod bilan biriktirish va ulash** ni bosing. Bildirishnoma paydo bo‘ladi. Telegramda `/phone` bilan tekshiring.
7. Telefon fayl qabul qilsin desangiz ilovadagi **yangi fayl nusxalarini qabul qilish** tugmasini yoqing.

Telefon va kompyuter turli Wi-Fi yoki mobil internetda bo‘lishi mumkin. Kompyuter yoqilgan, bot+tunnel ishlayotgan va telefon internetda bo‘lishi kerak. Telefon o‘chirilsa/offline bo‘lsa ish bajarilmaydi. Har 10 soniyada tekshiradi; internet va Android quvvat siyosati kechiktirishi mumkin. Android servisni to‘xtatsa ilovadan qayta boshlang; Samsung ilova batareya cheklovini sozlash kerak bo‘lishi mumkin. Qayta yoqilganda yashirin avtomatik ishga tushmaydi. Bu versiyada 24/7 kafolat yo‘q.
Bot qayta ochilsa qayta `/phonepair`; tunnel qayta ochilsa yangi HTTPS manzilini ham kiriting.

## Buyruq misollari
```
/devices
/pcroots
/pcfind dissertatsiya
/pcget hujjat/dissertatsiya.pdf
/pcread hujjat/eslatma.txt
/pcedit hujjat/eslatma.txt | eski jumla | yangi jumla
/pcapply BOT_BERGAN_KOD
/phone
/phonefind pdf
/phoneget QIDIRUV_BERGAN_ID
/phoneput hujjat/tahrirlangan.pdf
/phoneoff
```
Fayl yo‘li buyruqda papka aliasidan boshlanadi. Masalan papka `C:\Users\PC-11\Documents\Ish` va alias `hujjat` bo‘lsa shu papkadagi `reja.txt` yo‘li `hujjat/reja.txt`.
Fayl hajmi 4 MiB gacha. Matn tahriri UTF-8 fayl<=256KiB, eski/yangi qism<=1000 belgi va eski qism aynan bir marta uchrashi kerak. Preview muddati5 daqiqa; shu orada fayl o‘zgarsa tahrir qo‘llanmaydi. Zaxiralar `state/file_backups`, telefondan olingan nusxalar `phone_received`, Telegramga yuborilgan PC nusxalari `exports/personal` da saqlanadi; ularni davriy o‘zingiz tozalang.
Telefonga yuborish asl faylni almashtirmaydi: `Agentlar_ID_...` nomli yangi nusxa yaratadi. Telefon qidiruvi500 yozuv/10 daraja, PC10000 yozuv/12 daraja, natija40tagacha. Topilmasa aniqroq kichik papka tanlang. Telefon navbati10 amal; har birining muddati5 daqiqa.

## To‘xtatish va ruxsatlarni bekor qilish
Telefon ilovasi/bildirishnomadagi **To‘xtatish** aloqani to‘xtatadi. `/phoneoff` kompyuter tomondagi tokenni bekor qiladi va navbatni tozalaydi. Allaqachon boshlangan fayl amali tugab qolishi mumkin. PC papka ruxsatini olib tashlash uchun botni to‘xtating va lokal config.json dagi pc_folders dan tegishli aliasni o‘chiring. Token/API kalit/config.json ni hech kimga yubormang.
APK ichida Telegram/Gemini kalitlari yo‘q; telefon bir martalik koddan olingan alohida sessiya tokenini saqlaydi. Faqat egasining private Telegram chatidagi buyruqlar qabul qilinadi. HTTP relay Bearer tokensiz fayl/navbatga ruxsat bermaydi; transport HTTPS tunneldan o‘tadi. Cloudflare va Telegram orqali ma’lumot uzatiladi; bu xizmatlardan xoli end-to-end tizim emas.

## Tekshiruv holati va manbalar
Python testlari, haqiqiy lokal HTTP autentifikatsiya/navbat testlari, Android Java kompilyatsiyasi, APK v2/v3 imzosi tekshirildi. Samsung A30s ga shu muhitdan o‘rnatish va haqiqiy Internet juftlash sinovi bajarilmagan; birinchi amaliy tekshiruv `/phone` → `/phonefind` → `/phoneget`.
Rasmiy hujjatlar:
- https://developer.android.com/training/data-storage/shared/documents-files
- https://developers.cloudflare.com/tunnel/get-started/quick-tunnels/

## Android manba kodidan APK yig‘ish
Tayyor APK paketda bor. Qayta yig‘ish uchun JDK (javac/java/keytool), Android SDK Platform30 va Build-Tools34.0.0 o‘rnating. Android Studio SDK Manager orqali olinadi. `android` papkasida:
```
py -3 build_android.py --sdk "%LOCALAPPDATA%\Android\Sdk"
```
Bu misol CMD uchun; PowerShell da `py -3 build_android.py --sdk "$env:LOCALAPPDATA\Android\Sdk"`.
Mahalliy development imzolash kaliti yaratiladi; uni saqlang, tarqatmang. Dastlabki APK boshqa development kaliti bilan imzolangan: o‘zingiz qayta yig‘gan APKni o‘rnatish uchun eski APKni o‘chirib qayta o‘rnatish kerak bo‘lishi mumkin (papka ruxsati va ulanishni qayta sozlaysiz). Play Store relizi emas.
