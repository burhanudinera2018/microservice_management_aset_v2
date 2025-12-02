from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class AsetSawah(db.Model):
    __tablename__ = 'aset_sawah'
    aset_id = db.Column(db.Integer, primary_key=True)
    nama_sebutan = db.Column(db.String(255), nullable=False)
    nomor_sertifikat = db.Column(db.String(100), unique=True, nullable=False)
    luas_m2 = db.Column(db.Numeric(10, 2), nullable=False)
    luas_boto = db.Column(db.Numeric(10, 2))
    lokasi = db.Column(db.String(200), nullable=False)
    tanaman_saat_ini = db.Column(db.String(100))
    status_sewa = db.Column(db.String(50), nullable=False, default='Tersedia')
    tanggal_dibuat = db.Column(db.DateTime, default=datetime.utcnow)

    transaksi = db.relationship('TransaksiSewa', back_populates='aset', cascade='all, delete-orphan')


class Penyewa(db.Model):
    __tablename__ = 'penyewa'
    penyewa_id = db.Column(db.Integer, primary_key=True)
    nama_lengkap = db.Column(db.String(255), nullable=False)
    nik = db.Column(db.String(20), unique=True, nullable=False)
    alamat = db.Column(db.Text)
    nomor_kontak = db.Column(db.String(50))

    # 🚨 TAMBAHKAN KOLOM INI 🚨
    link_ktp = db.Column(db.String(255))

    transaksi = db.relationship('TransaksiSewa', back_populates='penyewa', cascade='all, delete-orphan')

class TransaksiSewa(db.Model):
    __tablename__ = 'transaksi_sewa'
    sewa_id = db.Column(db.Integer, primary_key=True)
    aset_id = db.Column(db.Integer, db.ForeignKey('aset_sawah.aset_id', ondelete='CASCADE'))
    penyewa_id = db.Column(db.Integer, db.ForeignKey('penyewa.penyewa_id', ondelete='CASCADE'))

    # TAMBAHKAN KOLOM WAJIB: FOREIGN KEY KE RIWAYAT HARGA
    harga_sewa_id = db.Column(db.Integer, db.ForeignKey('harga_sewa.id'), nullable=False)
    
    tanggal_mulai = db.Column(db.Date, nullable=False)
    tanggal_akhir = db.Column(db.Date, nullable=False)
    durasi_bulan = db.Column(db.Integer, nullable=False)
    nilai_sewa = db.Column(db.Numeric(15, 2), nullable=False)
    # 🚨 PERBAIKAN & PENAMBAHAN STATUS BAYAR 🚨
    status_pembayaran = db.Column(db.String(50), nullable=False, default='Belum Bayar')
    jenis_tanaman_disepakati = db.Column(db.String(100))
    tanggal_transaksi = db.Column(db.DateTime, default=datetime.utcnow)

    # TAMBAHKAN RELATIONSHIP
    
    aset = db.relationship('AsetSawah', back_populates='transaksi')
    penyewa = db.relationship('Penyewa', back_populates='transaksi')
    harga = db.relationship('HargaSewa') 
    
    # Kolom ini harus sesuai dengan nama kolom di database Anda
    link_bukti_bayar = db.Column(db.Text) 
    # Pastikan nama atribut di sini sama persis dengan nama kolom di DB
    # Jika nama kolom di DB adalah 'link_bukti_bayar', maka atribut Model juga harus 'link_bukti_bayar'
    tanggal_transaksi = db.Column(db.TIMESTAMP(timezone=False), default=db.func.now())

    # management_service/models/aset_model.py (Tambahkan di bagian akhir)

# ... (setelah class TransaksiSewa) ...

# --- MODEL HARGA SEWA (Diperlukan untuk Foreign Key di TransaksiSewa) ---
class HargaSewa(db.Model):
    __tablename__ = 'harga_sewa'
    id = db.Column(db.Integer, primary_key=True)
    harga_per_boto = db.Column(db.Numeric(10, 2), nullable=False)
    # Tambahkan kolom riwayat harga sesuai rancangan
    tanggal_mulai_efektif = db.Column(db.Date)
    tanggal_akhir_efektif = db.Column(db.Date)
    tahun_penetapan = db.Column(db.Integer)
    tanggal_diperbarui = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    

    # management_service/models/aset_model.py (Tambahkan ini)

# ... (Definisi class TransaksiSewa) ...


