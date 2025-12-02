#import GeoAlchemy2
from flask import Blueprint, render_template, redirect, url_for, flash
from sqlalchemy import func # Pastikan ini diimpor
from decimal import Decimal # Pastikan ini diimpor
#from geoalchemy2 import Geometry
from models.aset_model import db, AsetSawah
from src.forms import AsetForm
from sqlalchemy.exc import SQLAlchemyError

aset_bp = Blueprint('aset', __name__, url_prefix='/aset')

@aset_bp.route('/list')
def list_aset():
    # KRITIS: Menggunakan db.session.query() untuk mengekstrak Longitude dan Latitude
    data = db.session.query(
        AsetSawah, # Objek AsetSawah yang utuh
        func.ST_X(AsetSawah.lokasi).label('longitude'), # Ekstrak Longitude (X)
        func.ST_Y(AsetSawah.lokasi).label('latitude')   # Ekstrak Latitude (Y)
    ).order_by(AsetSawah.aset_id.desc()).all()
    
    # Data dikirim ke template sebagai list of SQLAlchemy Row objects.
    # Di template, ini akan diakses sebagai a[0] (objek AsetSawah), a.longitude, a.latitude.
    return render_template('list_aset.html', data=data)

# FILE: aset_routes.py (Fungsi tambah_aset)

@aset_bp.route('/tambah', methods=['GET', 'POST'])
def tambah_aset():
    form = AsetForm()
    
    if form.validate_on_submit():
        
        # --- 1. KONVERSI LOKASI KE WKT UNTUK POSTGIS ---
        lokasi_mentah = form.lokasi.data.strip()
        try:
            # Memisahkan Longitude dan Latitude (dipisahkan koma, sesuai forms.py)
            lon, lat = map(str.strip, lokasi_mentah.split(',')) 
            
            # Membuat string format WKT: 'POINT(Longitude Latitude)'
            lokasi_wkt = f'POINT({lon} {lat})' 
        
        except Exception:
            # Ini hanya sebagai fallback, form validation seharusnya sudah menangani ini
            flash('ERROR: Gagal memproses format koordinat untuk database.', 'danger')
            return render_template('form_aset.html', form=form, title='Tambah Aset Sawah') 

        # --- 2. PERHITUNGAN OTOMATIS luas_boto (Konversi Decimal ke Float) ---
        luas_m2_data = form.luas_m2.data
        try:
            # Mengkonversi Decimal ke float sebelum dibagi dengan float (14.0)
            luas_boto_terhitung = float(luas_m2_data) / 14.0 
        except Exception:
            # Fallback jika luas_m2 bukan angka
            luas_boto_terhitung = 0.0 
        
        aset = AsetSawah(
            nama_sebutan=form.nama_sebutan.data,
            nomor_sertifikat=form.nomor_sertifikat.data,
            luas_m2=luas_m2_data,
            luas_boto=luas_boto_terhitung,
            # Menggunakan nilai yang sudah dikonversi ke WKT
            lokasi=lokasi_wkt, 
            tanaman_saat_ini=form.tanaman_saat_ini.data,
            status_sewa=form.status_sewa.data
        )
        try:
            db.session.add(aset)
            db.session.commit()
            flash('Aset berhasil ditambahkan', 'success')
            return redirect(url_for('aset.list_aset'))
        
        except SQLAlchemyError as e:
            db.session.rollback()
            # ... (kode error handling database lainnya tetap sama) ...
            if 'duplicate key value violates unique constraint' in str(e):
                flash('ERROR: Nomor Sertifikat sudah digunakan. Data tidak tersimpan.', 'danger')
            else:
                flash(f'ERROR DB: Gagal menyimpan data aset. {e}', 'danger')
            
            return render_template('form_aset.html', form=form, title='Tambah Aset Sawah') 
            
    

    else:
        # **TAMBAHKAN DEBUGGING DI SINI**
        flash('ERROR Validasi Form: Pastikan semua kolom terisi dengan benar.', 'danger')
        print("!!! FORM VALIDATION FAILED:")
        for fieldName, errorMessages in form.errors.items():
            for err in errorMessages:
                print(f"  - {fieldName}: {err}")
                flash(f"Validasi Gagal di {fieldName}: {err}", 'danger')
            
    return render_template('form_aset.html', form=form, title='Tambah Aset Sawah')
        
        
# FILE: aset_routes.py (Koreksi fungsi edit_aset)

@aset_bp.route('/edit/<int:aset_id>', methods=['GET', 'POST'])
def edit_aset(aset_id):
    aset = AsetSawah.query.get_or_404(aset_id)
    form = AsetForm(obj=aset)
    
    if form.validate_on_submit():
        
        luas_m2_data = form.luas_m2.data
        
        # 🚨 BLOK TRY-EXCEPT UNTUK MENANGKAP ERROR KONVERSI DATA 🚨
        try:
            # 1. KONVERSI LOKASI KE POSTGIS GEOMETRY
            lokasi_mentah = form.lokasi.data.strip()
            lon, lat = map(str.strip, lokasi_mentah.split(','))
            
            # Set objek Geometry secara manual ke ORM
            aset.lokasi = func.ST_GeomFromText(f'POINT({lon} {lat})', 4326) 
            
            # 2. KONVERSI DATA NUMERIK (Luas)
            # Menghandle input lokal (misal '2.290,00') menjadi Decimal yang valid ('2290.00')
            if isinstance(luas_m2_data, str):
                # Hapus titik (separator ribuan) dan ganti koma menjadi titik (separator desimal)
                luas_str_normalized = luas_m2_data.replace('.', '').replace(',', '.')
                luas_m2_decimal = Decimal(luas_str_normalized)
            else:
                luas_m2_decimal = Decimal(luas_m2_data)

            # Set luas_m2 dan hitung luas_boto menggunakan nilai Decimal yang sudah dinormalisasi
            aset.luas_m2 = luas_m2_decimal
            aset.luas_boto = luas_m2_decimal / Decimal(14) 
            
            # 3. UPDATE FIELD LAIN SECARA MANUAL
            aset.nama_sebutan = form.nama_sebutan.data
            aset.nomor_sertifikat = form.nomor_sertifikat.data
            aset.tanaman_saat_ini = form.tanaman_saat_ini.data
            aset.status_sewa = form.status_sewa.data
            
            # 4. COMMIT
            db.session.commit()
            flash('Aset berhasil diperbarui', 'info')
            return redirect(url_for('aset.list_aset'))
        
        except SQLAlchemyError as e:
            db.session.rollback()
            # 🚨 LOGGING DITINGKATKAN UNTUK MENDAPATKAN ERROR DB SPESIFIK 🚨
            import logging
            logging.basicConfig(level=logging.ERROR) # Pastikan logging diaktifkan
            logging.error(f"SQLAlchemy UPDATE ASET GAGAL: {e}")
            if 'duplicate key value violates unique constraint' in str(e):
                flash('ERROR: Nomor Sertifikat sudah digunakan. Data tidak tersimpan.', 'danger')
            else:
                flash(f'ERROR DB KRITIS: Gagal memperbarui data aset. Cek log server.', 'danger') 
            
        except Exception as e:
            # Tangkap error Python umum (misal ValueError dari map() atau Decimal)
            flash(f'ERROR DATA: Gagal mengkonversi data numerik/koordinat. Detail: {e}', 'danger')
            
        # Jika terjadi error (DB atau Python), render ulang form
        return render_template('form_aset.html', form=form, aset=aset) 
            
    # GET Request atau Form Gagal Validasi
    return render_template('form_aset.html', form=form, aset=aset)


@aset_bp.route('/delete/<int:aset_id>', methods=['POST'])
def delete_aset(aset_id):
    aset = AsetSawah.query.get_or_404(aset_id)
    db.session.delete(aset)
    db.session.commit()
    flash('Aset berhasil dihapus', 'warning')
    return redirect(url_for('aset.list_aset'))


