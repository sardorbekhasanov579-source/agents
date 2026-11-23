# V1.2 tekshiruv hisoboti — 2026-11-17

45/45 unittest PASS, offline demo PASS, compileall PASS.
Linuxda haqiqiy Python venv/unittest va Node/npm install/test/build bajarildi.
Mustaqil ko‘rikdagi 5 muammo regressiya testlari bilan tuzatildi: stale dist, ZIP/source xesh qayta tekshiruvi, lockfile xeshi/arxivga kiritilishi, toza Python venv, Telegram/Gemini retry siyosatlarini ajratish.
Windows qurilmasi, Windows Job Object va foydalanuvchi kalitlari bilan jonli API sinovi bajarilmagan.
Qarorlar: Windows-native web/Python birinchi; WSL/Android keyingi bosqich. Local build bir martalik local opt-in bilan host huquqida ishlaydi, sandbox emas. Static profil brauzer testi deb ko‘rsatilmaydi. Testlar butun mahsulot xatosizligini kafolatlamaydi.

V1.2.1: 49/49 test PASS. Real SQLite faylida o‘qish xatosi takrorlandi va tuzatildi; ikkilik fayl baytlari o‘zgarmasligi va UTF-8 bo‘lmagan manba jim tasdiqlanmasligi tekshirildi.

## v1.3 (2026-11-17)
62 Python tests passed, including local HTTP auth/pair/revoke/queue/file-result flow, owner access, stale edit protection, backup, directory budget, long preview rejection and slow client concurrency. Android Java PairGate test passed. Full APK compiled and signature verified v2/v3. Actual Samsung A30s/Windows junction/live tunnel interaction not exercised in this environment. See TELEFON_PC_QOLLANMA.md for first-device check.
