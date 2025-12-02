# management_service/main.py (KODE FINAL TERKOREKSI DAN STABIL)

import os
import requests 
from datetime import date
from dotenv import load_dotenv

# Tambahkan 'send_from_directory' untuk menayangkan file upload (KTP)
from flask import Flask, render_template, redirect, url_for, flash, request, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
# Import semua yang dibutuhkan dari wtforms (Hanya di main.py jika model ada di sini)
from wtforms import StringField, DecimalField, SelectField, SubmitField, IntegerField, TextAreaField, DateField
from wtforms.validators import DataRequired, Length
from sqlalchemy.exc import SQLAlchemyError
from decimal import Decimal 
from sqlalchemy import func # Diperlukan untuk perhitungan statistik

# --- PENTING ---
# 1. Import objek db global dari aset_model (db = SQLAlchemy())
# 2. Import semua Model dari models/aset_model.py
from models.aset_model import db, AsetSawah, Penyewa, TransaksiSewa, HargaSewa 

# Import Forms (Asumsikan Form Anda ada di src/forms.py)
from src.forms import AsetForm, PenyewaForm, TransaksiForm, HargaForm # Pastikan HargaForm diimport

# Import Blueprints (Menggunakan impor sederhana yang sudah diperbaiki)
from src.routes.aset_routes import aset_bp
from src.routes.penyewa_routes import penyewa_bp
from src.routes.transaksi_routes import transaksi_bp


# ===============================================
# KONSTANTA MICROSERVICE
# ===============================================
# Ambil dari env atau default ke 5003
PRICING_SERVICE_URL = os.getenv('PRICING_SERVICE_URL', "http://localhost:5003") 

# ---------------------------------------------------\
# 1. SETUP APLIKASI DAN DATABASE 
# ---------------------------------------------------\

load_dotenv()
app = Flask(__name__)

# Tentukan direktori root project
BASE_DIR = os.path.abspath(os.path.dirname(__file__))\

# Konfigurasi Upload:
UPLOAD_FOLDER = os.path.join(os.path.dirname(BASE_DIR), 'uploads')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024 # Batas 16MB

# Konfigurasi DB
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev_secret')


# --- PERBAIKAN KRITIS: INIT DB ---
# Hubungkan objek db yang diimport dari aset_model ke aplikasi Flask
db.init_app(app) 

# Cek dan buat folder uploads jika belum ada
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)


# ---------------------------------------------------\
# 3. DAFTARKAN BLUEPRINTS
# ---------------------------------------------------\

app.register_blueprint(aset_bp)
app.register_blueprint(penyewa_bp)
app.register_blueprint(transaksi_bp, url_prefix='/transaksi')


# ---------------------------------------------------\
# 4. ROUTE UTAMA DAN SISTEM
# ---------------------------------------------------\

# ROUTE DASHBOARD UTAMA
@app.route('/')
def index():
    """Menampilkan dashboard utama dengan ringkasan statistik."""
    try:
        total_aset = db.session.query(AsetSawah).count()
        aset_tersedia = db.session.query(AsetSawah).filter_by(status_sewa='Tersedia').count()
        total_penyewa = db.session.query(Penyewa).count()
        total_transaksi = db.session.query(TransaksiSewa).count()
        
    except SQLAlchemyError as e:
        # Jika database belum siap atau ada masalah koneksi
        flash(f'Gagal mengambil statistik database: {e}', 'danger')
        total_aset = aset_tersedia = total_penyewa = total_transaksi = 0

    context = {
        'total_aset': total_aset,
        'aset_tersedia': aset_tersedia,
        'total_penyewa': total_penyewa,
        'total_transaksi': total_transaksi
    }
    
    # render_template('index.html') akan berhasil karena file sudah ada dan terdaftar
    return render_template('index.html', context=context)


# ROUTE WAJIB: MENAYANGKAN FILE UPLOAD (KTP, dll.)
# Route ini memungkinkan file diakses melalui URL: /uploads/namafile.jpg
@app.route('/uploads/<path:filename>')
def uploaded_file(filename):
    # Menggunakan path:filename untuk menangani subdirektori (walaupun tidak digunakan saat ini)
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


# ROUTE PENGATURAN HARGA (Jika Anda ingin mengelola harga di Management Service)
@app.route('/pengaturan/harga', methods=['GET', 'POST'])
def pengaturan_harga():
    # Karena HargaSewa sudah ada di models/aset_model.py, ini akan menggunakan DB yang sama
    harga = HargaSewa.query.first()
    form = HargaForm(obj=harga)

    if form.validate_on_submit():
        if harga:
            harga.harga_per_boto = form.harga_per_boto.data
            flash('Harga sewa per boto berhasil diperbarui!', 'success')
        else:
            new_harga = HargaSewa(harga_per_boto=form.harga_per_boto.data)
            db.session.add(new_harga)
            flash('Harga sewa per boto berhasil disimpan!', 'success')
            
        try:
            db.session.commit()
            return redirect(url_for('pengaturan_harga'))
        except SQLAlchemyError as e:
            db.session.rollback()
            flash(f'Gagal menyimpan harga: {e}', 'danger')


    return render_template('form_pengaturan_harga.html', form=form, title='Pengaturan Harga Sewa')


# ---------------------------------------------------\
# 5. RUN APLIKASI
# ---------------------------------------------------\

if __name__ == '__main__':
    with app.app_context():
        # JANGAN gunakan db.create_all() secara otomatis di sini jika Anda menggunakan Alembic/migrasi
        # Tetapi jika Anda yakin ingin membuatnya secara otomatis: db.create_all()
        pass
    app.run(debug=True, port=5002) # Port 5002 untuk Management Service