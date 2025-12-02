from flask_wtf import FlaskForm
from wtforms import DecimalField, SubmitField, DateField, IntegerField
from wtforms.validators import DataRequired, NumberRange, ValidationError
from decimal import Decimal
from datetime import date

class HargaForm(FlaskForm):
    """
    Formulir untuk menetapkan harga sewa per boto, termasuk periode efektif
    dan tahun penetapan untuk mendukung riwayat harga.
    """
    harga_per_boto = DecimalField('Harga Sewa per Boto (Rp)', validators=[DataRequired()], places=2)
    
    tanggal_mulai_efektif = DateField('Mulai Efektif', format='%Y-%m-%d', validators=[DataRequired()])
    tanggal_akhir_efektif = DateField('Akhir Efektif', format='%Y-%m-%d', validators=[DataRequired()])
    
    # Tahun Penetapan (biasanya hanya tahun)
    tahun_penetapan = IntegerField('Tahun Penetapan', validators=[
        DataRequired(), 
        NumberRange(min=2000, message='Tahun penetapan harus 4 digit dan valid.')
    ])

    submit = SubmitField('Simpan Pengaturan Harga')

    # Custom validator untuk memastikan tanggal mulai tidak lebih besar dari tanggal akhir
    def validate_tanggal_akhir_efektif(self, field):
        """
        Memastikan Tanggal Akhir Efektif terjadi setelah Tanggal Mulai Efektif.
        """
        if self.tanggal_mulai_efektif.data and field.data:
            if field.data <= self.tanggal_mulai_efektif.data:
                raise ValidationError("Tanggal Akhir Efektif harus setelah Tanggal Mulai Efektif.")

    # Custom validator untuk memastikan tahun penetapan sesuai dengan tanggal mulai
    def validate_tahun_penetapan(self, field):
        """
        Memastikan Tahun Penetapan sama dengan tahun pada Tanggal Mulai Efektif.
        """
        if self.tanggal_mulai_efektif.data and field.data:
            if field.data != self.tanggal_mulai_efektif.data.year:
                raise ValidationError("Tahun Penetapan harus sama dengan tahun di Tanggal Mulai Efektif.")

    # Custom validator untuk memastikan harga > 0
    def validate_harga_per_boto(self, field):
        if field.data <= Decimal(0):
            raise ValidationError("Harga per boto harus lebih besar dari nol.")