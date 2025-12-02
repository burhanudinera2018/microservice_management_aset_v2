# FILE: management_service/src/routes/transaksi_routes.py (KOREKSI TOTAL)

from flask import Blueprint, render_template, redirect, url_for, flash, current_app, request
from models.aset_model import db, TransaksiSewa, AsetSawah, Penyewa, HargaSewa 
from src.forms import TransaksiForm
import requests 
from decimal import Decimal 
from sqlalchemy.exc import SQLAlchemyError 
import json 
from wtforms.validators import DataRequired 
from datetime import datetime # Diperlukan untuk tanggal transaksi dan timestamp
from werkzeug.utils import secure_filename 
import os
import uuid 
import logging
from sqlalchemy import func # Diperlukan untuk update query

# Konfigurasi logger
logging.basicConfig(level=logging.INFO)

transaksi_bp = Blueprint('transaksi', __name__)
# ---------------------------------------------------------------------
# 1. ROUTE DAFTAR TRANSAKSI (List Transaksi)
# ---------------------------------------------------------------------

@transaksi_bp.route('/list')
def list_transaksi():
    try:
        data = TransaksiSewa.query.order_by(TransaksiSewa.sewa_id.desc()).all()
    except SQLAlchemyError as e:
        flash(f'Gagal mengambil data transaksi: {e}', 'danger')
        data = []
    return render_template('list_transaksi.html', data=data, title='Daftar Transaksi Sewa')

# ---------------------------------------------------------------------
# 1.1 ROUTE LIST TRANSAKSI BERDASARKAN ID HARGA (list_by_harga)
# ---------------------------------------------------------------------

@transaksi_bp.route('/list_by_harga/<int:harga_id>')
def list_by_harga(harga_id):
    """Menampilkan daftar transaksi yang menggunakan ID harga sewa tertentu."""
    
    try:
        data = TransaksiSewa.query.filter_by(harga_sewa_id=harga_id).order_by(TransaksiSewa.sewa_id.desc()).all()
        
        harga_obj = HargaSewa.query.get(harga_id) 
        harga_label = f"Harga ID {harga_id}"
        if harga_obj:
            harga_label = f"Rp {harga_obj.harga_per_boto:,.0f} (Tahun {harga_obj.tahun_penetapan})"
        
    except SQLAlchemyError as e:
        flash(f'Gagal mengambil data transaksi: {e}', 'danger')
        data = []
        harga_label = f"Harga ID {harga_id}"
        
    flash(f'Menampilkan transaksi untuk penetapan harga: {harga_label}', 'info')
    
    return render_template('list_transaksi.html', 
                           data=data, 
                           title=f'Transaksi untuk Harga: {harga_label}')

# ---------------------------------------------------------------------
# 2. ROUTE TAMBAH TRANSAKSI (Dengan Pemilihan Harga API)
# ---------------------------------------------------------------------

@transaksi_bp.route('/tambah', methods=['GET', 'POST'])
def tambah_transaksi():
    form = TransaksiForm()
    
    PRICING_SERVICE_URL = current_app.config.get('PRICING_SERVICE_URL', 'http://127.0.0.1:5003')
    harga_list = [] 

    # --- FASE 1: MEMUAT PILIHAN HARGA DARI API ---
    try:
        response = requests.get(f'{PRICING_SERVICE_URL}/api/v1/harga/list_all')
        response.raise_for_status() 
        harga_list = response.json()
        
        form.harga_pilihan_id.choices = [(h['id'], h['label']) for h in harga_list]
        
    except requests.exceptions.RequestException:
        flash('ERROR API: Gagal terhubung/merespons dari Layanan Harga. Pastikan Pricing Service berjalan.', 'danger')
        form.harga_pilihan_id.choices = [] 
    except (KeyError, ValueError, IndexError):
        flash('ERROR DATA: Format data harga dari API tidak valid.', 'danger')
        form.harga_pilihan_id.choices = []

    # --- FASE 2: MEMUAT PILIHAN ASET & PENYEWA (Lokal) ---
    form.aset_id.choices = [(0, '--- Pilih Aset ---')] + [(a.aset_id, a.nama_sebutan) for a in AsetSawah.query.order_by(AsetSawah.aset_id).all()]
    form.penyewa_id.choices = [(0, '--- Pilih Penyewa ---')] + [(p.penyewa_id, p.nama_lengkap) for p in Penyewa.query.order_by(Penyewa.penyewa_id).all()]


    if form.validate_on_submit():
        
        # --- FASE 3: LOGIC PENYIMPANAN DATA ---
        
        # 1. Ambil data harga yang dipilih
        harga_dipilih = next((h for h in harga_list if h['id'] == form.harga_pilihan_id.data), None)
        
        if not harga_dipilih:
            flash('Harga yang dipilih tidak valid atau data harga API hilang. Coba lagi.', 'danger')
            return render_template('form_transaksi.html', form=form)

        # 2. Ambil data dan Hitung Nilai Sewa
        harga_id_digunakan = harga_dipilih['id'] 
        
        try:
            # Mengambil harga mentah (Tarif untuk 100 boto/tahun)
            harga_100_boto = Decimal(harga_dipilih['harga_per_boto']) 
            
            # 🚨 KOREKSI MATH: Hitung HARGA PER 1 BOTO per TAHUN (Dibagi 100) 🚨
            harga_per_1_boto_annual = harga_100_boto / Decimal(100)
            
        except Exception:
             flash('ERROR: Harga per boto tidak dapat dikonversi menjadi angka.', 'danger')
             return render_template('form_transaksi.html', form=form)
        
        
        aset = db.session.get(AsetSawah, form.aset_id.data)
        
        if aset and aset.luas_boto is not None:
            luas_boto = aset.luas_boto
        else:
            flash('ERROR: Data luas boto aset tidak ditemukan atau nol.', 'danger')
            return render_template('form_transaksi.html', form=form)
            
        durasi = form.durasi_bulan.data
        
        # 3. Hitung Total Sewa (LOGIC MATEMATIKA FINAL)
        
        # Total Sewa Tahunan = Luas Boto * Harga per 1 Boto Tahunan
        total_annual_rent = luas_boto * harga_per_1_boto_annual
        
        # Total Sewa Akhir = Total Tahunan * (Durasi Bulan / 12)
        total_sewa = total_annual_rent * (Decimal(durasi) / Decimal(12)) 


        tr = TransaksiSewa(
            aset_id=form.aset_id.data,
            penyewa_id=form.penyewa_id.data,
            tanggal_mulai=form.tanggal_mulai.data,
            tanggal_akhir=form.tanggal_akhir.data,
            durasi_bulan=form.durasi_bulan.data,
            jenis_tanaman_disepakati=form.jenis_tanaman_disepakati.data,
            nilai_sewa=total_sewa,
            harga_sewa_id=harga_id_digunakan,
            # Isi status dan tanggal transaksi awal
            status_pembayaran=form.status_pembayaran.data, 
            tanggal_transaksi=datetime.now() # Menggunakan datetime.now() untuk timestamp
        )
        
        # 4. Update Status Aset dan Commit
        if aset:
            aset.status_sewa = 'Disewa'
            
        db.session.add(tr)
        
        try:
            db.session.commit()
            flash('Transaksi berhasil dibuat dan aset diperbarui!', 'success')
            return redirect(url_for('transaksi.list_transaksi'))

        except SQLAlchemyError as e:
            db.session.rollback()
            logging.error(f"ERROR DB (tambah_transaksi): {e}")
            flash('ERROR DB: Gagal menyimpan transaksi. Cek log database.', 'danger')
            return render_template('form_transaksi.html', form=form, title='Tambah Transaksi')
            
    else:
        # FASE 4: DEBUGGING VALIDASI (Ketika Form Gagal di-submit)
        if request.method == 'POST':
            flash('ERROR VALIDASI: Data tidak tersimpan. Periksa semua kolom.', 'danger')
            for fieldName, errorMessages in form.errors.items():
                for err in errorMessages:
                    flash(f"Validasi Gagal di {fieldName}: {err}", 'danger') 

    return render_template('form_transaksi.html', form=form, title='Tambah Transaksi')

# ---------------------------------------------------------------------
# 3. ROUTE EDIT TRANSAKSI
# ---------------------------------------------------------------------

@transaksi_bp.route('/edit/<int:sewa_id>', methods=['GET', 'POST']) 
def edit_transaksi(sewa_id):
    """Mengubah data transaksi yang sudah ada."""
    
    transaksi = db.session.get(TransaksiSewa, sewa_id)
    if transaksi is None:
        flash('Transaksi tidak ditemukan.', 'danger')
        return redirect(url_for('transaksi.list_transaksi'))
        
    form = TransaksiForm(obj=transaksi)

    # --- FASE 1: MEMUAT PILIHAN HARGA DARI API ---
    PRICING_SERVICE_URL = current_app.config.get('PRICING_SERVICE_URL', 'http://127.0.0.1:5003')
    harga_list = []
    
    try:
        response = requests.get(f'{PRICING_SERVICE_URL}/api/v1/harga/list_all')
        response.raise_for_status() 
        harga_list = response.json()
        
        form.harga_pilihan_id.choices = [(h['id'], h['label']) for h in harga_list]

        if request.method == 'GET' and transaksi.harga_sewa_id:
             form.harga_pilihan_id.data = transaksi.harga_sewa_id
        
    except requests.exceptions.RequestException:
        flash('ERROR API: Gagal terhubung/merespons dari Layanan Harga (Port 5003).', 'danger')
        form.harga_pilihan_id.choices = [] 
    except (KeyError, ValueError):
        flash('ERROR DATA: Format data harga dari API tidak valid.', 'danger')
        form.harga_pilihan_id.choices = []
    
    # --- FASE 2: MEMUAT PILIHAN ASET & PENYEWA (Lokal) ---
    form.aset_id.choices = [(0, '--- Pilih Aset ---')] + [(a.aset_id, a.nama_sebutan) for a in AsetSawah.query.order_by(AsetSawah.aset_id).all()]
    form.penyewa_id.choices = [(0, '--- Pilih Penyewa ---')] + [(p.penyewa_id, p.nama_lengkap) for p in Penyewa.query.order_by(Penyewa.penyewa_id).all()]

    if form.validate_on_submit():
    # --- LOGIKA PERHITUNGAN DAN UPDATE ---
        
        # 1. Ambil data harga yang dipilih
        harga_dipilih = next((h for h in harga_list if h['id'] == form.harga_pilihan_id.data), None)
        
        if not harga_dipilih:
            flash('Harga yang dipilih tidak valid atau data harga API hilang. Coba lagi.', 'danger')
            return render_template('form_transaksi.html', form=form, transaksi=transaksi)

        # 2. Ambil data dan Hitung Nilai Sewa
        harga_id_digunakan = harga_dipilih['id'] 
        
        try:
            harga_100_boto = Decimal(harga_dipilih['harga_per_boto'])
            # 🚨 KOREKSI MATH: Hitung HARGA PER 1 BOTO per TAHUN (Dibagi 100) 🚨
            harga_per_1_boto_annual = harga_100_boto / Decimal(100)
        except Exception:
             flash('ERROR: Harga per boto tidak dapat dikonversi menjadi angka.', 'danger')
             return render_template('form_transaksi.html', form=form, transaksi=transaksi)
        
        # Dapatkan data aset baru atau yang lama
        aset = db.session.get(AsetSawah, form.aset_id.data)
        
        if aset and aset.luas_boto is not None:
            luas_boto = aset.luas_boto
        else:
            flash('ERROR: Data luas boto aset tidak ditemukan atau nol.', 'danger')
            return render_template('form_transaksi.html', form=form, transaksi=transaksi)
            
        durasi = form.durasi_bulan.data
        
        # 3. Hitung Total Sewa (LOGIC MATEMATIKA FINAL)
        total_annual_rent = luas_boto * harga_per_1_boto_annual
        total_sewa = total_annual_rent * (Decimal(durasi) / Decimal(12))


        # 4. Update objek transaksi dengan data baru
        form.populate_obj(transaksi)
        transaksi.nilai_sewa = total_sewa
        transaksi.harga_sewa_id = harga_id_digunakan 
        transaksi.tanggal_transaksi = datetime.now() # Update timestamp saat di edit
        
        # Update status aset lama (jika aset_id berubah, ini perlu logika tambahan)
        if aset:
            aset.status_sewa = 'Disewa' 

        try:
            db.session.commit()
            flash('Transaksi berhasil diperbarui!', 'success')
            return redirect(url_for('transaksi.list_transaksi'))
            
        except SQLAlchemyError as e:
            db.session.rollback()
            logging.error(f"ERROR DB (edit_transaksi): {e}")
            flash(f'Gagal memperbarui transaksi: {e}', 'danger')
            
    # Render form edit
    return render_template('form_transaksi.html', form=form, title='Edit Transaksi Sewa', transaksi=transaksi)

# ---------------------------------------------------------------------
# 4. ROUTE HAPUS TRANSAKSI
# ---------------------------------------------------------------------

@transaksi_bp.route('/hapus/<int:sewa_id>', methods=['POST'])
def hapus_transaksi(sewa_id):
    """Menghapus data transaksi."""
    transaksi = db.session.get(TransaksiSewa, sewa_id)
    if transaksi:
        
        db.session.delete(transaksi)
        try:
            db.session.commit()
            flash(f'Transaksi ID {sewa_id} berhasil dihapus.', 'success')
        except SQLAlchemyError:
             db.session.rollback()
             flash(f'Gagal menghapus transaksi. Cek log.', 'danger')
        
    return redirect(url_for('transaksi.list_transaksi'))


# ---------------------------------------------------------------------
# 5. ROUTE UPLOAD BUKTI BAYAR (Fiture Baru)
# ---------------------------------------------------------------------

@transaksi_bp.route("/upload-bukti-bayar", methods=['POST'])
def upload_bukti_bayar():
    sewa_id_str = request.form.get('sewa_id')
    file = request.files.get('file')
    
    if not sewa_id_str or not file:
        flash("Permintaan tidak valid. ID Transaksi atau File tidak ditemukan.", "danger")
        return redirect(url_for('transaksi.list_transaksi'))

    try:
        sewa_id = int(sewa_id_str)
    except ValueError:
        flash("ID Transaksi tidak valid.", "danger")
        return redirect(url_for('transaksi.list_transaksi'))

    transaksi = db.session.get(TransaksiSewa, sewa_id)
    
    # GUARD CHECKS: Status Lunas
    if not transaksi:
        flash("Transaksi tidak ditemukan.", "danger")
        return redirect(url_for('transaksi.list_transaksi'))

    if getattr(transaksi, 'status_pembayaran', 'Belum Bayar') != 'Lunas': 
        flash("Upload hanya dapat dilakukan untuk transaksi berstatus Lunas.", 'danger')
        return redirect(url_for('transaksi.list_transaksi'))
    
    # 3. Validasi Tipe File dan Keamanan
    ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png', 'pdf'}
    filename = secure_filename(file.filename)
    
    if '.' not in filename or filename.rsplit('.', 1)[1].lower() not in ALLOWED_EXTENSIONS:
        flash("Format file tidak didukung. Gunakan JPG, PNG, atau PDF.", 'danger')
        return redirect(url_for('transaksi.list_transaksi'))

    # 4. Proses Penyimpanan File
    UPLOAD_FOLDER = current_app.config['UPLOAD_FOLDER']
    BUKTI_BAYAR_DIR = os.path.join(UPLOAD_FOLDER, 'bukti_bayar')
    
    if not os.path.exists(BUKTI_BAYAR_DIR):
        os.makedirs(BUKTI_BAYAR_DIR)
        
    file_extension = filename.rsplit('.', 1)[1].lower()
    unique_filename = f"{uuid.uuid4().hex}.{file_extension}"
    file_path_full = os.path.join(BUKTI_BAYAR_DIR, unique_filename)

    file.save(file_path_full)
    
    # 5. Buat Path Relatif
    db_link = os.path.join('bukti_bayar', unique_filename).replace('\\', '/')
    
    # 6. Update Database MENGGUNAKAN QUERY (Final Fix)
    
    # Menggunakan objek Kolom Model untuk mengatasi masalah ORM state dan Unconsumed Column Name
    data_update = {
        TransaksiSewa.link_bukti_bayar: db_link, 
        TransaksiSewa.tanggal_transaksi: datetime.now() 
    }
    
    try:
        # Gunakan synchronize_session='fetch' untuk memastikan state sesi diperbarui
        db.session.query(TransaksiSewa).filter_by(sewa_id=sewa_id).update(data_update, synchronize_session='fetch')
        db.session.commit()
        flash('Bukti pembayaran berhasil diupload dan database diperbarui!', 'success')
        return redirect(url_for('transaksi.list_transaksi'))

    except SQLAlchemyError as e: 
        db.session.rollback()
        
        # Hapus file yang sudah di-upload jika gagal di DB
        if os.path.exists(file_path_full):
            os.remove(file_path_full)
            
        logging.error(f"SQLAlchemy UPDATE GAGAL: {e}") 
        flash('ERROR KRITIS: Gagal menyimpan data ke DB. Cek log server.', 'danger')
        return redirect(url_for('transaksi.list_transaksi'))