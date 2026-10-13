# Website Rumah Kreasi

Website katalog berbasis Flask dengan tema cream, responsif untuk HP/desktop, akun pelanggan, dashboard admin, upload katalog/logo/banner, dan chat langsung pelanggan-admin (bukan AI).

## Fitur
- Katalog kosong saat awal: tidak ada produk simulasi. Admin mengunggah produk asli.
- Dua koleksi sesuai daftar: KIDS COLLECTION dan GIFT & SOUVENIR.
- Login/daftar pelanggan dan login admin terpisah.
- Chat pelanggan ke admin, pesan tersimpan di database; dashboard admin menampilkan inbox dan jumlah pesan belum dibaca.
- Admin bisa unggah foto produk, mengatur produk unggulan "Best seller Batam", logo toko, banner halaman depan, judul/tagline, serta link Shopee dan Lynk.id.
- Tautan WhatsApp, TikTok, Instagram, dan Lynk.id Rumah Kreasi.
- Produk tanpa harga di katalog; tombol tanya admin via WhatsApp dan chat website.

## Menjalankan di komputer
Disarankan Python 3.11+.

1. Ekstrak ZIP ini.
2. Buat virtual environment lalu install:
   `python -m venv .venv`
   Windows: `.venv\\Scripts\\activate`
   macOS/Linux: `source .venv/bin/activate`
   `pip install -r requirements.txt`
3. Set environment variables SEBELUM menjalankan:
   Windows PowerShell:
   `$env:SECRET_KEY="buat-random-panjang"`
   `$env:ADMIN_EMAIL="email-admin-kamu"`
   `$env:ADMIN_PASSWORD="password-admin-kuat-minimal-12-karakter"`
   macOS/Linux:
   `export SECRET_KEY="buat-random-panjang"`
   `export ADMIN_EMAIL="email-admin-kamu"`
   `export ADMIN_PASSWORD="password-admin-kuat-minimal-12-karakter"`
4. Jalankan `python app.py`
5. Buka `http://127.0.0.1:5000`
6. Login admin melalui `/masuk` menggunakan email/password yang di-set, lalu buka Dashboard.

Catatan: akun admin hanya dibuat otomatis ketika ADMIN_EMAIL dan ADMIN_PASSWORD diset saat pertama kali database dibuat. Jangan gunakan password default atau deploy dengan SECRET_KEY yang belum diganti.

## Deploy online
Bisa dideploy ke layanan yang mendukung Python/Flask seperti Render atau VPS:
- Build/install: `pip install -r requirements.txt`
- Start command: `gunicorn app:app`
- Set environment variables `SECRET_KEY`, `ADMIN_EMAIL`, `ADMIN_PASSWORD`, `DATABASE_PATH`.
- Gunakan disk/volume persisten untuk `rumahkreasi.db` DAN folder `static/uploads`; tanpa penyimpanan persisten foto dan database dapat hilang saat redeploy.
- Aktifkan HTTPS.
- Untuk membuat website benar-benar online, kamu masih perlu akun hosting dan menghubungkan domain (jika punya).

## Tautan sosial
- TikTok: https://www.tiktok.com/@rumahkreasi.btm
- Instagram: https://www.instagram.com/rumahkreasi.btm/
- WhatsApp: https://wa.me/6285128002246
- Lynk.id default: https://lynk.id/rumahkreasi060224_
- URL Shopee belum diisi karena nama toko saja belum memastikan URL toko yang tepat. Isi di Dashboard > Tampilan website.

## Penting
- Chat menggunakan polling berkala (bukan WebSocket push), sehingga pesan muncul otomatis setelah beberapa detik selama halaman terbuka.
- Website ini adalah paket aplikasi siap dijalankan/deploy, bukan situs yang sudah dipublikasikan di internet. Belum ada domain/hosting yang disambungkan.
- Untuk produksi publik, set SECRET_KEY kuat, pakai HTTPS, backup database/uploads, dan pertimbangkan rate limiting, email reset password, serta aturan privasi.
