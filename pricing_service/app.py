# FILE: pricing_service/app.py

from flask import Flask, jsonify
import os
from dotenv import load_dotenv
from datetime import date 
from sqlalchemy.exc import SQLAlchemyError # Tambahkan untuk penanganan error DB
from sqlalchemy import func # Tambahkan jika diperlukan

# --- PASTIKAN FILE PENDUKUNG ADA & IMPORT BENAR ---\
# 1. db_instance.py: Harus berisi db = SQLAlchemy() dan definisi model HargaSewa
from .db_instance import db, HargaSewa, TransaksiSewa # Pastikan TransaksiSewa diimpor jika diperlukan
# 2. pricing_routes.py: Blueprint untuk rute web UI
from .routes.pricing_routes import harga_bp
import locale # Untuk pemformatan mata uang lokal

def format_currency(value):
    """Memformat nilai numerik ke format mata uang Rupiah (IDR)."""
    if value is None:
        return ""
    
    # Contoh pemformatan kustom (lebih aman dan universal di server)
    try:
        # Mengubah Decimal/float menjadi string format Rupiah
        # Misal: 4000000.00 menjadi Rp 4.000.000,00
        return f"Rp {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except ValueError:
        return str(value)

load_dotenv()

# --- DEFINISIKAN CONFIG CLASS DI SINI (Wajib untuk mengatasi 'config not found') ---\
class Config:
    """Konfigurasi Dasar untuk Pricing Service"""
    # Ambil konfigurasi dari environment variables
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL') 
    SECRET_KEY = os.getenv('SECRET_KEY_PRICING', 'price_secret') 
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
def create_app(config_class=Config):
    app = Flask(__name__)
    
    # KOREKSI: Gunakan from_mapping() untuk memuat konfigurasi dari Config Class secara langsung.
    # Ini menyelesaikan ERROR: 'config' not found.
    app.config.from_mapping(
        SQLALCHEMY_DATABASE_URI=config_class.SQLALCHEMY_DATABASE_URI,
        SECRET_KEY=config_class.SECRET_KEY,
        SQLALCHEMY_TRACK_MODIFICATIONS=config_class.SQLALCHEMY_TRACK_MODIFICATIONS
    )
    # --- PENDAFTARAN FILTER JINJA2 ---\
    # Daftarkan fungsi format_currency agar bisa dipanggil di template
    app.jinja_env.filters['format_currency'] = format_currency

    # INISIALISASI DB DAN BLUEPRINT
    db.init_app(app) # db diimpor dari .db_instance
    app.register_blueprint(harga_bp)
    
    return app

# --- PEMANGGILAN APLIKASI UTAMA (HANYA SEKALI) ---\
app = create_app()


# =====================================================================
# --- API ENDPOINT (Wajib oleh Management Service) ---
# =====================================================================

# 1. API: HARGA SAAT INI (get_current_price)
@app.route('/api/v1/harga/boto/current', methods=['GET'])
def get_current_price():
    """Mengembalikan harga sewa per boto yang paling baru dan masih berlaku hari ini."""
    today = date.today() 
    
    # Cari harga yang TANGGAL MULAI EFEKTIF-nya sudah berlaku dan paling baru
    harga = HargaSewa.query.filter(
        HargaSewa.tanggal_mulai_efektif <= today 
    ).order_by(
        HargaSewa.tanggal_mulai_efektif.desc() 
    ).first()
    
    if harga:
        return jsonify({
            'harga_id': harga.id,
            'harga_per_boto': str(harga.harga_per_boto), # Kirim sebagai string agar aman
            'tahun_penetapan': harga.tahun_penetapan
        }), 200
    else:
        # Jika tidak ada harga yang berlaku
        return jsonify({
            'harga_id': None, 
            'harga_per_boto': '0', 
            'tahun_penetapan': None,
            'message': 'Tidak ada harga sewa per boto yang berlaku saat ini.'
        }), 404

# 2. API: LIST SEMUA HARGA (list_all_harga - Dipindahkan dari pricing_routes.py)
@app.route('/api/v1/harga/list_all', methods=['GET'])
def list_all_harga():
    """Mengembalikan daftar semua harga (ID, Harga, Tahun) dalam format JSON."""
    
    try:
        # Ambil semua harga yang pernah ditetapkan
        riwayat = HargaSewa.query.order_by(HargaSewa.tanggal_mulai_efektif.desc()).all()
        
        data = [{
            'id': h.id, 
            # Label yang mudah dibaca di dropdown Management Service
            'label': f"Rp {h.harga_per_boto:,.0f} (Tahun {h.tahun_penetapan}, Mulai {h.tanggal_mulai_efektif.strftime('%d-%m-%Y') if h.tanggal_mulai_efektif else 'N/A'})",
            'harga_per_boto': str(h.harga_per_boto) # Harus string agar aman dalam JSON
        } for h in riwayat]
        
        return jsonify(data), 200
    
    except Exception as e:
        # Jika ada error database atau lainnya
        return jsonify({
            'error': 'Gagal mengambil data harga.',
            'details': str(e)
        }), 500