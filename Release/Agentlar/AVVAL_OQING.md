# Shaxsiy zaxira va Agentlar · Windows hamda Android sinov paketi

1. ZIPni to‘liq chiqaring. Windows’da Python 3.11+ va internet orqali zaxiralash uchun Cloudflared kerak. Cloudflared o‘rnatish buyrug‘i: `winget install --id Cloudflare.cloudflared -e`.
2. Windows’da `BOSHLASH.bat` faylini oching. Birinchi ishga tushirishda u Telegram bot va Gemini hisobini sozlaydi. Avvalgi sozlama bilan ishlash uchun uni zaxiralang va ushbu papkaga `config.json` faylini ko‘chiring. Eski bot jarayonini to‘xtating. HTTPS oynasidagi manzilni yozib oling.
3. Android’da `Shaxsiy_Zaxira_0_1.apk` ni o‘rnating. Shaxsiy botingizga `/zpair` yozing, ilovaga kod va HTTPS manzilini kiriting. Tizim oynasidan faylni tanlab yuboring. Har fayl uchun chegara 10 MiB.
4. Telefonni aviarejimga o‘tkazing va Telegram Desktop’dan botga «Diplomimni top» deb yozing. Mos natijadagi `/zol_…` buyrug‘i faylni yuboradi. «O‘tgan oy saqlagan diplomimni topib ber» so‘rovi nomida “diplom” bor va oldingi kalendar oyida zaxiralangan fayllarni ko‘rsatadi. Sana Windows kompyuteri vaqt mintaqasiga bog‘liq.
5. Botga dastur talabi yozing. `/status` bosqichni, `/files ID` tayyor loyiha arxivini ko‘rsatadi. Windows’da yig‘ish uchun `4_LOCAL_BUILD_SOZLASH.bat` bilan kerakli vositalarni tekshiring va yig‘ishni yoqing. Tanlangan PC papkalarini ulash uchun `5_PC_PAPKA_SOZLASH.bat` va botdagi `/devices` bo‘limidan foydalaning. O‘zgartirish uchun alohida ish papkasidagi loyiha bilan `/change ID yangi talab` ishlatiladi.

Ombor Windows kompyuterida AES-256-GCM bilan shifrlanadi. Telefon o‘chiq bo‘lganda tiklash uchun Windows kompyuteri va bot ishlab turishi kerak. Ombor va kalitni birga zaxiralash tartibi `0_ZAXIRA_BOSHLASH.md` faylida.

Bu paketda avvalgi Android APK ishlatilgan. Sinovda fayllar qo‘lda yuboriladi, qidiruv fayl nomi va zaxira sanasi bo‘yicha ishlaydi. SMS/Gmail tasdiqlashi, tiklash kodi, biometrik kirish, avtomatik media va kontakt zaxirasi, xarita, hujjat mazmuni bo‘yicha AI qidiruv, hosting va iPhone versiyasi ishlab chiqilishi kerak. Windows BAT fayllarini va jonli Android–Telegram ulanishini egasining qurilmasida sinash kerak.
