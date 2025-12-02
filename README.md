* **Deskripsi Proyek**
  
- Membangun sistem informasi pengelolaan aset lahan sawah menggunakan Python dan basis data PostgreSQL dengan ekstensi PostGIS dengan konsep Microservice,
- Di dalam direktori proyek management_aset_sawah_v2.
- Sistem ini akan mencatat properti lahan, detail sebagai berikut;
- Mencatat aset lahan sawah yang terdiri atas informasi ( bisa di edit dan delete );
    - Nama Sebutan sawah
    - Luas dalam m2
    - Luas dalam satuan bata
    - Memberikan koordinat lokasi yang tersambung ke Google Maps
    - Status lahan (Available, Disewa, Expired )
    - Foto lokasi sawah bisa dilihat dengan click link access `pic_object_aset`
    - Keterangan tambahan
- Mencatat Transaksi Sewa aset_lahan :
    - Sewa lahan selama kurun waktu tertentu
    - Biaya sewa Total dari harga yang di tepatkan persatuan luas tertentu dan penyewa tertentu dikenakan tarif tertentu
    - Jenis tanaman yang di tanaman.
    - Merujuk pada nama penyewa tertentu dengan penetapan harga yang di tetapkan dalam system
    - Bisa dilakukan tindakan ( Delete, Edit dan Upload pic tanda pelunasan pembayaran dalam format *.png)
- Mencatat Data penyewa terdiri atas:
      - Nama Penyewa
      - Alamat Penyewa
      - Lampiran KTP yang dapat di upload ke system dan di simpan
      - Nomor sellular
      - Nomor whatsApp
- Menu pengaturan penetapan harga sewa untuk tahun tahun tertentu yang mampu:
    - Ditampilkan dalam bentuk list harga yang pernah di tetapkan
    - Tahun penetapan harga sewa
- Bisa di jalankan di localhost dan bisa juga di letakkan pada free cloud server app
  * **Struktur Microservice** (Jelaskan ada `management_service` dan `pricing_service`).
```
MANAGEMENT_ASET_SAWAH (Root Directory)
├── database/                   # Skema dan migrasi database (misal: init.sql, migrasi/)
├── management_service/         # Microservice Utama (Manajemen Aset dan Transaksi)
│   ├── models/                 # Definisi model SQLAlchemy
│   ├── src/                    # Kode sumber utama (misal: service-specific logic)
│   ├── templates/              # File HTML/Jinja2 untuk Web UI
│   ├── venv_m/                 # Virtual Environment untuk Management Service (DIABAIKAN oleh Git)
│   ├── .env                    # Variabel environment (DIABAIKAN oleh Git)
│   ├── main.py                 # Titik masuk utama aplikasi (Main Flask App)
│   └── requirements.txt        # Daftar dependency Python
├── pricing_service/            # Microservice Harga (Penetapan dan Riwayat Harga)
│   ├── __pycache__/            # Cache Python (DIABAIKAN oleh Git)
│   ├── routes/                 # Definisi route/endpoint (misal: pricing_routes.py)
│   ├── templates/              # File HTML/Jinja2 untuk Web UI
│   ├── venv/                   # Virtual Environment untuk Pricing Service (DIABAIKAN oleh Git)
│   ├── .env                    # Variabel environment (DIABAIKAN oleh Git)
│   ├── app.py                  # Titik masuk utama aplikasi (Flask App)
│   ├── config.py               # Konfigurasi aplikasi (misal: Config Class)
│   ├── db_instance.py          # Konfigurasi koneksi DB dan instance SQLAlchemy
│   ├── forms.py                # Definisi WTForms
│   └── requirements.txt        # Daftar dependency Python
├── uploads/                    # Folder untuk menyimpan file yang diunggah pengguna (Disimpan sebagai kosong dengan .gitkeep)
│   └── .gitkeep                # File dummy agar folder dilacak Git
├── .env.example                # Contoh template konfigurasi environment (TIDAK ADA credential sensitif)
└── .gitignore                  # Daftar file/folder yang diabaikan Git (.env, venv, dll.)
```  
  * **Langkah Instalasi:**
    1.  `git clone ...`
    2.  `cd management_service`
    3.  `python3 -m venv venv_m`
    4.  `source venv_m/bin/activate`
    5.  `pip install -r requirements_1.txt`
    6.  *Ulangi untuk `pricing_service`.*
  * **Konfigurasi Environment:**
      * Sertakan contoh file **`.env.example`** (tanpa nilai sensitif) di *root* folder, dan arahkan pengguna untuk menyalinnya menjadi **`.env`** dan mengisi nilai yang benar.
  
  * **Cara Menjalankan Aplikasi** (misalnya, perintah Flask atau Gunicorn).
    ### 1\. Menjalankan Aplikasi Management Service (Port 5002)
    Aplikasi Management Service sepertinya berada di `management_service/src/app.py` atau `management_service/main.py`. Berdasarkan struktur umum, saya akan berasumsi file utama adalah **`management_service/main.py`** atau **`management_service/src/main.py`**.

**Buka Terminal 1:**

```bash
# 1. Atur FLASK_APP ke file yang berisi instance Flask di management_service
# Asumsi file utamanya adalah management_service/main.py
export FLASK_APP=management_service.main

# 2. Atur port untuk Management Service
export FLASK_RUN_PORT=5002

# 3. Jalankan aplikasi menggunakan Flask CLI
flask run
```

  * Aplikasi Management Service sekarang akan berjalan di: **`http://127.0.0.1:5002/`**

-----

### 2\. Menjalankan Aplikasi Pricing Service (Port 5003)

Aplikasi Pricing Service berada di `pricing_service/app.py`.

**Buka Terminal 2:**

```bash
# 1. Atur FLASK_APP ke file yang berisi instance Flask di pricing_service
export FLASK_APP=pricing_service.app

# 2. Atur port untuk Pricing Service
export FLASK_RUN_PORT=5003

# 3. Jalankan aplikasi menggunakan Flask CLI
flask run
```

  * Aplikasi Pricing Service sekarang akan berjalan di: **`http://127.0.0.1:5003/`**

-----
