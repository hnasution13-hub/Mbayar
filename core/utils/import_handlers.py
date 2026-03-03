# ==================================================
# FILE: core/utils/import_handlers.py
# PATH: D:/Project Pyton/Mbayar/core/utils/import_handlers.py
# FUNGSI: Handler untuk proses import berbagai tipe data
# ==================================================

import pandas as pd
from django.db import transaction
import logging

logger = logging.getLogger(__name__)

class BaseImportHandler:
    """Base class untuk semua import handler"""
    
    def __init__(self, file, user=None):
        self.file = file
        self.user = user
        self.results = {
            'total': 0,
            'success': 0,
            'failed': 0,
            'errors': [],
            'warnings': []
        }
    
    def read_file(self):
        """Baca file Excel/CSV ke DataFrame"""
        try:
            if self.file.name.endswith('.csv'):
                df = pd.read_csv(self.file)
            else:
                df = pd.read_excel(self.file)
            return df
        except Exception as e:
            logger.error(f"Error reading file: {e}")
            raise ValueError(f"Tidak dapat membaca file: {str(e)}")
    
    def validate_columns(self, df, required_columns):
        """Validasi kolom yang diperlukan"""
        missing = [col for col in required_columns if col not in df.columns]
        if missing:
            raise ValueError(f"Kolom berikut tidak ditemukan: {', '.join(missing)}")
        return True
    
    def clean_data(self, df):
        """Bersihkan data (hapus NaN, strip string, dll)"""
        # Hapus baris yang semua kolom kosong
        df = df.dropna(how='all')
        
        # Replace NaN dengan None atau 0
        df = df.where(pd.notnull(df), None)
        
        # Strip string untuk kolom teks
        for col in df.select_dtypes(include=['object']).columns:
            df[col] = df[col].astype(str).str.strip()
            df[col] = df[col].replace('None', None)
            df[col] = df[col].replace('nan', None)
        
        return df
    
    def process_row(self, row, index):
        """Process satu baris - harus diimplementasikan subclass"""
        raise NotImplementedError
    
    @transaction.atomic
    def process(self):
        """Process semua baris"""
        df = self.read_file()
        df = self.clean_data(df)
        
        self.results['total'] = len(df)
        
        for idx, row in df.iterrows():
            try:
                self.process_row(row, idx + 2)  # +2 karena Excel mulai baris 1 header, baris 2 data
                self.results['success'] += 1
            except Exception as e:
                self.results['failed'] += 1
                self.results['errors'].append({
                    'row': idx + 2,
                    'error': str(e)
                })
                logger.error(f"Error processing row {idx + 2}: {e}")
        
        return self.results


class KodeBarangImportHandler(BaseImportHandler):
    """Handler untuk import Kode Barang"""
    
    REQUIRED_COLUMNS = ['KODE', 'NAMA']
    
    def validate_columns(self, df):
        return super().validate_columns(df, self.REQUIRED_COLUMNS)
    
    def process_row(self, row, row_num):
        from ..models import KodeBarang
        
        kode = str(row.get('KODE', '')).strip()
        nama = str(row.get('NAMA', '')).strip()
        keterangan = str(row.get('KETERANGAN', '')) if pd.notnull(row.get('KETERANGAN')) else ''
        
        if not kode or not nama:
            raise ValueError("KODE dan NAMA harus diisi")
        
        # Cek duplikat
        existing = KodeBarang.objects.filter(kode=kode).first()
        if existing:
            # Update yang existing
            existing.nama = nama
            existing.keterangan = keterangan
            existing.save()
            self.results['warnings'].append({
                'row': row_num,
                'message': f"Kode {kode} sudah ada, data diupdate"
            })
        else:
            # Buat baru
            KodeBarang.objects.create(
                kode=kode,
                nama=nama,
                keterangan=keterangan
            )


class SupplierImportHandler(BaseImportHandler):
    """Handler untuk import Supplier"""
    
    REQUIRED_COLUMNS = ['NAMA']
    
    def validate_columns(self, df):
        return super().validate_columns(df, self.REQUIRED_COLUMNS)
    
    def process_row(self, row, row_num):
        from ..models import Supplier
        
        nama = str(row.get('NAMA', '')).strip()
        kontak = str(row.get('KONTAK', '')) if pd.notnull(row.get('KONTAK')) else ''
        telepon = str(row.get('TELEPON', '')) if pd.notnull(row.get('TELEPON')) else ''
        alamat = str(row.get('ALAMAT', '')) if pd.notnull(row.get('ALAMAT')) else ''
        
        if not nama:
            raise ValueError("NAMA harus diisi")
        
        Supplier.objects.create(
            name=nama,
            contact=kontak,
            phone=telepon,
            address=alamat
        )


class MenuImportHandler(BaseImportHandler):
    """Handler untuk import Menu dan Bahan"""
    
    def validate_columns(self, df):
        # Kolom minimal: KODE_MENU, NAMA_MENU
        required = ['KODE_MENU', 'NAMA_MENU']
        return super().validate_columns(df, required)
    
    @transaction.atomic
    def process(self):
        from ..models import Menu, MenuCategory, MenuIngredient, StockItem, KodeBarang
        
        df = self.read_file()
        df = self.clean_data(df)
        
        self.results['total'] = len(df)
        
        # Group by menu
        menus = {}
        for idx, row in df.iterrows():
            kode_menu = str(row.get('KODE_MENU', '')).strip()
            if kode_menu not in menus:
                menus[kode_menu] = {
                    'nama': str(row.get('NAMA_MENU', '')).strip(),
                    'kategori': str(row.get('KATEGORI', 'Umum')).strip(),
                    'bahan': []
                }
            
            # Tambah bahan jika ada
            if pd.notnull(row.get('KODE_BAHAN')):
                menus[kode_menu]['bahan'].append({
                    'kode_bahan': str(row.get('KODE_BAHAN')).strip(),
                    'jumlah': float(row.get('JUMLAH', 0)) if pd.notnull(row.get('JUMLAH')) else 0,
                    'catatan': str(row.get('CATATAN', '')) if pd.notnull(row.get('CATATAN')) else ''
                })
        
        # Process each menu
        for kode_menu, data in menus.items():
            try:
                # Buat atau update kategori
                category, _ = MenuCategory.objects.get_or_create(
                    name=data['kategori']
                )
                
                # Buat atau update menu
                menu, created = Menu.objects.update_or_create(
                    code=kode_menu,
                    defaults={
                        'name': data['nama'],
                        'category': category,
                        'is_available': True
                    }
                )
                
                if created:
                    self.results['success'] += 1
                else:
                    self.results['warnings'].append({
                        'message': f"Menu {kode_menu} diupdate"
                    })
                
                # Hapus bahan lama
                menu.menu_ingredients.all().delete()
                
                # Tambah bahan baru
                for bahan in data['bahan']:
                    try:
                        # Cari stock item berdasarkan kode barang
                        kode_barang = KodeBarang.objects.filter(kode=bahan['kode_bahan']).first()
                        if kode_barang:
                            stock_item = StockItem.objects.filter(kode_barang=kode_barang).first()
                            if stock_item:
                                MenuIngredient.objects.create(
                                    menu=menu,
                                    stock_item=stock_item,
                                    quantity_used=bahan['jumlah'],
                                    notes=bahan['catatan']
                                )
                            else:
                                self.results['warnings'].append({
                                    'message': f"Stock item untuk kode {bahan['kode_bahan']} tidak ditemukan"
                                })
                        else:
                            self.results['warnings'].append({
                                'message': f"Kode barang {bahan['kode_bahan']} tidak ditemukan"
                            })
                    except Exception as e:
                        self.results['warnings'].append({
                            'message': f"Error bahan {bahan['kode_bahan']}: {str(e)}"
                        })
                
            except Exception as e:
                self.results['failed'] += 1
                self.results['errors'].append({
                    'row': 'multiple',
                    'error': f"Menu {kode_menu}: {str(e)}"
                })
        
        return self.results


def get_import_handler(data_type, file, user=None):
    """Factory function untuk mendapatkan handler yang sesuai"""
    handlers = {
        'kode_barang': KodeBarangImportHandler,
        'supplier': SupplierImportHandler,
        'menu': MenuImportHandler,
    }
    
    handler_class = handlers.get(data_type)
    if not handler_class:
        raise ValueError(f"Tipe data {data_type} tidak dikenal")
    
    return handler_class(file, user)