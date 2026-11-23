# Google Drive bilan boshlash

Neon Free loyihasi: shaxsiy-zaxira (icy-unit-78968961). Baza: zaxira.
Google Drive bo‘sh joyi 4,9 GB bo‘lgani uchun ilova limiti 4,8 GB etib belgilangan. Boshqa Google xizmatlari joy ishlatsa, qolgan haqiqiy hajm kamayishi mumkin.

1. Windows’da GOOGLE_DRIVE_ULASH.bat faylini oching. Google hisobingizni tanlab ruxsat bering. Agar rclone o‘rnatilmagan bo‘lsa, oynada o‘rnatish buyrug‘i chiqadi.
2. GitHub’da shaxsiy bo‘sh shaxsiy-zaxira-cloud reposini yarating. README.md dagi buyruqlar bilan shu papka tarkibini push qiling. Sozlamalar va tokenlarni GitHub’ga joylamang.
3. Neon’da yuqoridagi loyiha → Connect → zaxira bazasining TLS ulanish satrini Render’dagi DATABASE_URL maydoniga kiriting.
4. Render → New → Blueprint orqali yangi reponi tanlang. ZAXIRA_REMOTE_CONFIG uchun birinchi qadamdagi qiymat kerak (BAT faylini qayta ochish shu qiymatni yana nusxalaydi). Telegram rekvizitlarini README.md bo‘yicha kiriting.
5. /health tekshiruvidan keyin Android ilovasiga yangi HTTPS manzil va botdagi /zpair kodini kiriting. Sinov faylini yuboring va Windows xizmati o‘chirilgan holda bot orqali qaytarib oching.
