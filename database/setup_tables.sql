-- Mengaktifkan ekstensi PostGIS
CREATE EXTENSION IF NOT EXISTS postgis;

-- 0. Hapus tabel anak terlebih dahulu (untuk pengujian ulang)

-- Urutan yang Benar: Hapus anak sebelum induk
DROP TABLE IF EXISTS transaksi_sewa; 
DROP TABLE IF EXISTS aset_sawah;    -- Kini dapat dihapus karena transaksi_sewa sudah hilang
DROP TABLE IF EXISTS penyewa;
DROP TABLE IF EXISTS harga_sewa;

-- (Kemudian lanjutkan dengan perintah CREATE TABLE)

-- 1. Tabel ASET_SAWAH (Properti Lahan)
-- Pastikan ekstensi PostGIS sudah diaktifkan di database Anda
-- Jika belum, jalankan: CREATE EXTENSION postgis;

CREATE TABLE aset_sawah (
    aset_id SERIAL PRIMARY KEY,
    nama_sebutan VARCHAR(255) NOT NULL,
    nomor_sertifikat VARCHAR(100) UNIQUE NOT NULL,
    luas_m2 NUMERIC(10, 2) NOT NULL,
    luas_boto NUMERIC(10, 2),
    lokasi GEOMETRY(Point, 4326), -- Tipe data PostGIS untuk menyimpan koordinat (SRID 4326 = WGS 84)
    status_sewa VARCHAR(50) DEFAULT 'Available',
    keterangan_tambahan TEXT,
    link_foto_lokasi TEXT
);

-- Opsional: Tambahkan indeks spasial untuk performa query berbasis lokasi
CREATE INDEX idx_aset_sawah_lokasi ON aset_sawah USING GIST (lokasi);

-- 2. Tabel PENYEWA (Data Identitas Penyewa) ... (sama seperti sebelumnya)
CREATE TABLE IF NOT EXISTS PENYEWA (
    penyewa_id SERIAL PRIMARY KEY,
    nama_lengkap VARCHAR(255) NOT NULL,
    nik VARCHAR(20) UNIQUE NOT NULL, -- NIK juga harus NOT NULL
    alamat TEXT,
    nomor_kontak VARCHAR(50),      -- Digunakan untuk nomor seluler
    nomor_whatsapp VARCHAR(50),    -- Kolom terpisah untuk WhatsApp (opsional, tapi lebih jelas)
    link_ktp TEXT                  -- Kolom baru untuk URL Lampiran KTP
);

-- 3. Tabel HARGA_SEWA
CREATE TABLE harga_sewa (
    id SERIAL PRIMARY KEY,
    harga_per_boto NUMERIC(10, 2) NOT NULL,
    tanggal_mulai_efektif DATE NOT NULL,
    tanggal_akhir_efektif DATE, -- NULL jika harga masih aktif/berlaku
    tahun_penetapan INTEGER,
    -- Opsional: Tambahkan kolom tanggal_diperbarui seperti di model Python Anda
    tanggal_diperbarui TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Opsional: Tambahkan CONSTRAINT untuk memastikan tanggal akhir selalu setelah tanggal mulai
ALTER TABLE harga_sewa
ADD CONSTRAINT check_tanggal_efektif
CHECK (tanggal_akhir_efektif IS NULL OR tanggal_akhir_efektif >= tanggal_mulai_efektif);


-- 4. Tabel TRANSAKSI_SEWA (Detail Sewa) ... (lakukan modifikasi dari sebelumnya)
CREATE TABLE transaksi_sewa (
    sewa_id SERIAL PRIMARY KEY,
    
    -- Foreign Key ke tabel aset_sawah
    aset_id INTEGER NOT NULL REFERENCES aset_sawah (aset_id) ON DELETE CASCADE,
    
    -- Foreign Key ke tabel penyewa
    penyewa_id INTEGER NOT NULL REFERENCES penyewa (penyewa_id) ON DELETE CASCADE,
    
    -- Foreign Key ke tabel harga_sewa (penting untuk riwayat harga)
    harga_sewa_id INTEGER NOT NULL REFERENCES harga_sewa (id),
    
    tanggal_mulai DATE NOT NULL,
    tanggal_akhir DATE NOT NULL,
    durasi_bulan INTEGER NOT NULL,
    nilai_sewa NUMERIC(15, 2) NOT NULL,
    jenis_tanaman_disepakati VARCHAR(100),
    link_bukti_bayar TEXT,
    
    -- Constraint untuk memastikan tanggal akhir tidak sebelum tanggal mulai
    CONSTRAINT check_tanggal_sewa_validity
    CHECK (tanggal_akhir >= tanggal_mulai)
);

