# FILE: pricing_service/routes/pricing_routes.py

from flask import Blueprint, render_template, redirect, url_for, flash, jsonify, request # Tambahkan request
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import func
import json 
from decimal import Decimal 
from datetime import date 

# PENTING: Import dari file-file lokal di pricing_service
# Asumsi db dan model berada di 'db_instance.py'
from ..db_instance import db, HargaSewa, TransaksiSewa 
# Asumsi form berada di 'forms.py'
from ..forms import HargaForm 
import os # Pastikan ini sudah diimpor
MANAGEMENT_SERVICE_URL = os.getenv('MANAGEMENT_SERVICE_URL', 'http://127.0.0.1:5002')

# Definisi Blueprint (URL prefix: /pengaturan/harga)
harga_bp = Blueprint('harga', __name__, url_prefix='/pengaturan/harga')

# ---------------------------------------------------------------------
## 1. ROUTE MENAMPILKAN RIWAYAT HARGA (WEB UI)
# ---------------------------------------------------------------------

@harga_bp.route('/list')
def list_harga():
    """Menampilkan riwayat harga sewa per boto, termasuk jumlah transaksi yang menggunakannya."""
    
    # Melakukan JOIN antara HargaSewa dan TransaksiSewa untuk menghitung jumlah transaksi
    riwayat_harga_query = db.session.query(
        HargaSewa, 
        # Menghitung jumlah transaksi yang menggunakan harga ini
        func.count(TransaksiSewa.sewa_id).label('jumlah_transaksi')
    ).outerjoin(TransaksiSewa, HargaSewa.id == TransaksiSewa.harga_sewa_id) \
    .group_by(HargaSewa.id) \
    .order_by(HargaSewa.tanggal_mulai_efektif.desc())
    
    try:
        data = riwayat_harga_query.all()
    except SQLAlchemyError as e:
        flash(f'Gagal mengambil data riwayat harga: {e}', 'danger')
        data = []
        
    # Tambahkan context URL
    return render_template('list_riwayat_harga.html', 
                            data=data, 
                            title='Riwayat Harga Sewa', 
                            management_url=MANAGEMENT_SERVICE_URL) # <--- TAMBAHKAN INI


# ---------------------------------------------------------------------\
## 2. ROUTE TAMBAH HARGA (WEB UI)\
# ---------------------------------------------------------------------\

@harga_bp.route('/tambah', methods=['GET', 'POST'])
def tambah_harga():
    """Menambahkan harga sewa per boto baru."""
    form = HargaForm()

    if form.validate_on_submit():
        # Lakukan pengecekan apakah rentang tanggal tumpang tindih (opsional, tapi disarankan)
        
        new_harga = HargaSewa(
            harga_per_boto=form.harga_per_boto.data,
            tanggal_mulai_efektif=form.tanggal_mulai_efektif.data,
            tanggal_akhir_efektif=form.tanggal_akhir_efektif.data,
            tahun_penetapan=form.tahun_penetapan.data
        )
        db.session.add(new_harga)
        try:
            db.session.commit()
            flash('Harga sewa per boto berhasil disimpan!', 'success')
            return redirect(url_for('harga.list_harga'))
        except SQLAlchemyError as e:
            db.session.rollback()
            flash(f'Gagal menyimpan harga: {e}', 'danger')

    elif request.method == 'POST':
        flash('ERROR Validasi Form: Pastikan semua kolom terisi dengan benar.', 'danger')
        # Debugging form.errors jika perlu
        # for fieldName, errorMessages in form.errors.items():
        #     for err in errorMessages:
        #         flash(f"Validasi Gagal di {fieldName}: {err}", 'danger')

    return render_template('form_harga.html', form=form, title='Tambah Harga Sewa')


# ---------------------------------------------------------------------\
## 3. ROUTE EDIT HARGA (WEB UI)\
# ---------------------------------------------------------------------\
@harga_bp.route('/edit/<int:harga_id>', methods=['GET', 'POST'])
def edit_harga(harga_id):
    """Mengedit data harga sewa per boto yang sudah ada."""
    harga = db.session.get(HargaSewa, harga_id)
    if harga is None:
        flash('Harga tidak ditemukan.', 'danger')
        return redirect(url_for('harga.list_harga'))
    
    # Gunakan HargaForm dengan data yang sudah ada
    form = HargaForm(obj=harga)

    if form.validate_on_submit():
        form.populate_obj(harga)
        try:
            db.session.commit()
            flash('Harga sewa berhasil diperbarui!', 'success')
            return redirect(url_for('harga.list_harga'))
        except SQLAlchemyError as e:
            db.session.rollback()
            flash(f'Gagal memperbarui harga: {e}', 'danger')

    return render_template('form_harga.html', form=form, title='Edit Harga Sewa', harga=harga)


# ---------------------------------------------------------------------\
## 4. ROUTE HAPUS HARGA (WEB UI)\
# ---------------------------------------------------------------------\
@harga_bp.route('/hapus/<int:harga_id>', methods=['POST'])
def hapus_harga(harga_id):
    """Menghapus data harga sewa per boto."""
    harga = db.session.get(HargaSewa, harga_id)
    if harga:
        try:
            db.session.delete(harga)
            db.session.commit()
            flash('Harga berhasil dihapus!', 'warning')
        except SQLAlchemyError as e:
            db.session.rollback()
            flash(f'Gagal menghapus harga. Pastikan harga ini tidak digunakan dalam transaksi. {e}', 'danger')
    
    return redirect(url_for('harga.list_harga'))


# --- ROUTE API: list_all_harga SUDAH DIHAPUS DARI FILE INI ---
# --- Rute API sekarang hanya ada di app.py: /api/v1/harga/boto/current dan /api/v1/harga/list_all ---