from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from models.aset_model import db, Penyewa
from src.forms import PenyewaForm
from werkzeug.utils import secure_filename
import os
from sqlalchemy.exc import SQLAlchemyError # Diperlukan untuk penanganan error DB

# Inisialisasi Blueprint
penyewa_bp = Blueprint('penyewa', __name__, url_prefix='/penyewa')

# 1. ROUTE LIST DATA PENYEWA
@penyewa_bp.route('/list')
def list_penyewa():
    """Menampilkan daftar semua data penyewa."""
    # Menambahkan try-except untuk penanganan error database
    try:
        data = Penyewa.query.order_by(Penyewa.penyewa_id.desc()).all()
    except SQLAlchemyError as e:
        flash(f'Gagal mengambil data penyewa dari database: {e}', 'danger')
        data = []
        
    return render_template('list_penyewa.html', data=data)

# 2. ROUTE TAMBAH DATA PENYEWA (Perbaikan: Redirect sudah benar)
@penyewa_bp.route('/tambah', methods=['GET', 'POST'])
def tambah_penyewa():
    """Menambahkan data penyewa baru."""
    form = PenyewaForm()
    
    if form.validate_on_submit():
        try:
            # --- LOGIKA UPLOAD FILE KTP ---
            link_ktp = None
            # 'ktp_file' harus sama dengan name di form_penyewa.html
            if 'ktp_file' in request.files: 
                file = request.files['ktp_file']
                
                # Memastikan file ada dan nama file tidak kosong
                if file and file.filename != '':
                    filename = secure_filename(file.filename)
                    
                    # Cek jika folder upload sudah ada
                    upload_folder = current_app.config.get('UPLOAD_FOLDER')
                    if not os.path.exists(upload_folder):
                        os.makedirs(upload_folder)
                        
                    # Simpan file
                    filepath = os.path.join(upload_folder, filename)
                    file.save(filepath)
                    
                    # Simpan link relatif (yang dapat diakses oleh browser)
                    link_ktp = os.path.join('/uploads', filename)
            
            # --- LOGIKA PENYIMPANAN DATA UTAMA ---
            p = Penyewa(
                nama_lengkap=form.nama_lengkap.data,
                nik=form.nik.data,
                alamat=form.alamat.data,
                nomor_kontak=form.nomor_kontak.data,
                link_ktp=link_ktp # <-- Simpan link file
            )
            
            db.session.add(p)
            db.session.commit()
            flash('Penyewa berhasil ditambahkan!', 'success')
            
            # PERBAIKAN PENTING: Gunakan 'penyewa.list_penyewa'
            return redirect(url_for('penyewa.list_penyewa')) 
            
        except SQLAlchemyError as e:
            db.session.rollback()
            flash(f'Gagal menambahkan penyewa ke database: {e}', 'danger')
            
    # Render template, tambahkan title dan pastikan form diisi
    return render_template('form_penyewa.html', form=form, title='Tambah Penyewa Baru')

# 3. ROUTE EDIT DATA PENYEWA (Fungsi Baru untuk mengatasi BuildError sebelumnya)
@penyewa_bp.route('/edit/<int:penyewa_id>', methods=['GET', 'POST'])
def edit_penyewa(penyewa_id):
    """Mengubah data penyewa yang sudah ada."""
    
    # Ambil data penyewa dari database, jika tidak ada kembalikan 404
    penyewa = db.session.get(Penyewa, penyewa_id)
    if penyewa is None:
        flash('Penyewa tidak ditemukan.', 'danger')
        return redirect(url_for('penyewa.list_penyewa'))
        
    # Inisialisasi form dengan data penyewa yang ada (pre-populate)
    form = PenyewaForm(obj=penyewa)
    
    if form.validate_on_submit():
        try:
            # Muat data dari form ke objek penyewa
            form.populate_obj(penyewa)
            
            # --- LOGIKA UPDATE FILE KTP (Jika ada file baru diupload) ---
            if 'ktp_file' in request.files: 
                file = request.files['ktp_file']
                
                if file and file.filename != '':
                    # Jika penyewa sudah memiliki file KTP, hapus file lama (Optional)
                    # if penyewa.link_ktp and os.path.exists(os.path.join(current_app.config['UPLOAD_FOLDER'], os.path.basename(penyewa.link_ktp))):
                    #     os.remove(os.path.join(current_app.config['UPLOAD_FOLDER'], os.path.basename(penyewa.link_ktp)))
                        
                    filename = secure_filename(file.filename)
                    upload_folder = current_app.config.get('UPLOAD_FOLDER')
                    filepath = os.path.join(upload_folder, filename)
                    file.save(filepath)
                    
                    # Update link KTP baru
                    penyewa.link_ktp = os.path.join('/uploads', filename)
            
            db.session.commit()
            flash('Data Penyewa berhasil diperbarui!', 'success')
            return redirect(url_for('penyewa.list_penyewa'))
            
        except SQLAlchemyError as e:
            db.session.rollback()
            flash(f'Gagal memperbarui penyewa: {e}', 'danger')
            
    # Render form edit
    return render_template('form_penyewa.html', form=form, title='Edit Data Penyewa', penyewa=penyewa)


# 4. ROUTE HAPUS DATA PENYEWA (CRUD Lengkap)
@penyewa_bp.route('/hapus/<int:penyewa_id>', methods=['POST'])
def hapus_penyewa(penyewa_id):
    """Menghapus data penyewa."""
    
    penyewa = db.session.get(Penyewa, penyewa_id)
    
    if penyewa is None:
        flash('Penyewa tidak ditemukan.', 'danger')
        return redirect(url_for('penyewa.list_penyewa'))
        
    try:
        # Hapus juga file KTP terkait (Optional, tapi disarankan)
        # if penyewa.link_ktp:
        #     # Cari path fisik file
        #     filename = os.path.basename(penyewa.link_ktp)
        #     filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
        #     if os.path.exists(filepath):
        #         os.remove(filepath)

        db.session.delete(penyewa)
        db.session.commit()
        flash(f'Penyewa ID {penyewa_id} berhasil dihapus.', 'success')
        
    except SQLAlchemyError as e:
        db.session.rollback()
        flash(f'Gagal menghapus penyewa: {e}', 'danger')
        
    return redirect(url_for('penyewa.list_penyewa'))