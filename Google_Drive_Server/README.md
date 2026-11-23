# Shaxsiy zaxira · GitHub, Render, Neon va tashqi ombor

Bu server Android 0.6 bilan ishlaydi. Render HTTPS so‘rovlarini qabul qiladi. Neon’da hisob, fayl identifikatorlari, shifrlangan nomlar va qisqa qidiruv matni turadi. Yangi faylning shifrlangan baytlari egasining bulutidagi ShaxsiyZaxira papkasiga yoziladi. Jami yangi va eski yozuvlar uchun dasturiy chegara 4,8 milliard bayt, 1000 nusxa. Har bir fayl uchun 10 MiB. Provayder hisobidagi real bo‘sh joy ham yetarli bo‘lishi kerak.

## 1. Fayllarni GitHub’ga chiqarish

ZIPni yangi papkaga to‘liq chiqaring. Ichida render.yaml va Dockerfile turgan papkani VS Code’da oching. GitHub’da shaxsiy bo‘sh repo yarating. VS Code terminalida quyidagini bajaring. REPO_URL o‘rniga aynan yangi repo HTTPS manzilini kiriting.

```powershell
git init -b main
git add .
git status --short
git commit -m "Prepare Shaxsiy Zaxira cloud server"
git remote add origin REPO_URL
git push -u origin main
```

## 2. Bulutni bog‘lash

Windows’da rclone o‘rnating. PowerShell’da alohida konfiguratsiyani loyiha tashqarisida yarating. Quyidagi fayl nomi mavjud bo‘lsa yangi nom tanlang.

```powershell
$cfg = Join-Path $env:LOCALAPPDATA 'shaxsiy-zaxira-remote.conf'
rclone config --config $cfg
```

New remote tanlang. Nomi aynan zaxira bo‘lsin. Provayderingizga qarab onedrive, drive yoki s3 turini tanlang. OneDrive/Google Drive uchun brauzerda o‘z hisobingizga ruxsat bering. S3 uchun bucketga o‘qish/yozish ruxsati bor rekvizitlar kerak. Konfiguratsiya bitta remote saqlashi kerak. Oddiy rclone konfiguratsiyasi ishlatiladi. Uni Render siriga nusxalash uchun:

```powershell
[Convert]::ToBase64String([IO.File]::ReadAllBytes($cfg)) | Set-Clipboard
```

Bu qiymat maxfiy. Render’dagi ZAXIRA_REMOTE_CONFIG maydoniga qo‘ying, GitHub yoki chatga yubormang. S3 ishlatilsa Render sozlamasiga ZAXIRA_BUCKET sifatida bucket nomini ham kiriting. Shifrlash kaliti va Neon ma’lumotlarining zaxirasini saqlang. Bulutdagi .bin fayllarini nomini o‘zgartirish yoki o‘chirish ularni tiklashga ta’sir qiladi.

## 3. Neon va Render

Neon’da loyiha uchun alohida bo‘sh baza oching. Connect oynasidagi TLS bilan himoyalangan PostgreSQL ulanish satrini oling. Render’da New → Blueprint orqali GitHub reposini tanlang. render.yaml repo ildizida. Render quyidagilarni so‘raydi:

| Render siri | Qiymat |
|---|---|
| DATABASE_URL | Neon ulanish satri |
| ZAXIRA_REMOTE_CONFIG | Yuqoridagi Base64 qiymati |
| TELEGRAM_OWNER_ID | Windows agentidagi config.json ichidagi owner_id raqami |
| TELEGRAM_BOT_TOKEN | Bulut zaxirasi uchun alohida BotFather boti tokeni |

WEBHOOK_SECRET va VAULT_MASTER_KEY yangi servisda avtomatik yaratiladi. VAULT_MASTER_KEY’ni parol menejeriga saqlang. Avvalgi Neon omborni davom ettirsangiz asl kalit va owner_id kerak. Windows botini alohida tokenida qoldiring. SMS/Gmail orqali yangi tiklash hisobini yaratish uchun TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_VERIFY_SERVICE_SID va tegishli provayder kanallari kerak. Bulut nusxalariga Telegram orqali kirish uchun Twilio talab qilinmaydi.

## 4. Sinash

Deploy tugagach xizmatning /health manzilini oching. Android 0.6 da server manzili sifatida Render bergan HTTPS manzilining o‘zini kiriting. Yangi botga /zpair yuboring, kod bilan telefonni ulang. Bitta kichik sinov faylini yuboring. Windows xizmatini to‘xtating va boshqa qurilmadagi Telegram orqali /zaxira hamda /zol_… bilan faylni qaytarib oching. Boshqa qurilmadan hisob orqali tiklash uchun /zregister bilan tiklash hisobini oldindan ro‘yxatdan o‘tkazing.

Oldin Windows’da saqlangan fayllarni alohida tanlab yangi omborga yuboring. Eski omborni va kalitni saqlab turing. Render Free uyqudan uyg‘onganda birinchi so‘rov kechikishi mumkin.
