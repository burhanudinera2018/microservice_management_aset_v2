from flask_sqlalchemy import SQLAlchemy

# Hanya membuat objek db, tanpa menginisialisasi dengan app
db = SQLAlchemy()

# Anda bisa menempatkan definisi model di sini atau di file models.py terpisah

# --- MODEL HARGA ---
class HargaSewa(db.Model):
    __tablename__ = 'harga_sewa'
    id = db.Column(db.Integer, primary_key=True)
    harga_per_boto = db.Column(db.Numeric(10, 2), nullable=False) 
    
    # TAMBAHAN UNTUK RIWAYAT HARGA
    tanggal_mulai_efektif = db.Column(db.Date, nullable=False)
    tanggal_akhir_efektif = db.Column(db.Date, nullable=False)
    tahun_penetapan = db.Column(db.Integer, nullable=False)
    
    tanggal_diperbarui = db.Column(db.DateTime, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())
    
    # PENTING: Anda mungkin perlu menghapus dan membuat ulang tabel 'harga_sewa' di DB
    # setelah perubahan ini agar kolom baru terdaftar.

# --- MODEL TRANSAKSI (HANYA UNTUK KEPERLUAN QUERY JUMLAH TRANSAKSI) ---
class TransaksiSewa(db.Model):
    __tablename__ = 'transaksi_sewa'
    sewa_id = db.Column(db.Integer, primary_key=True)
    harga_sewa_id = db.Column(db.Integer, db.ForeignKey('harga_sewa.id'))
    # Anda hanya perlu mendefinisikan kolom yang penting untuk relasi
    # Kolom lain bisa disingkat atau dihilangkan jika tidak diperlukan di pricing service