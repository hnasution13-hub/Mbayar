# Mbayar POS

Aplikasi Point of Sale (POS) berbasis web untuk restoran, kafe, dan UMKM. 
Dibangun dengan Django dan Bootstrap, mendukung manajemen stok, menu, multi‑outlet, dan laporan keuangan.

## Fitur Utama
- Kasir dengan keranjang belanja dan opsi GoFood
- Manajemen stok & pembelian (harga rata‑rata tertimbang)
- Manajemen menu & bahan baku (HPP otomatis)
- Multi‑outlet (cabang) dengan stok terpisah/terpusat
- Laporan penjualan, laba rugi, stok (export Excel/PDF)
- Manajemen pengguna dengan role (admin, supervisor, kasir, owner)
- Backup & restore database
- Import data dari Excel/CSV

## Persyaratan Sistem
- Python 3.8+
- Django 4.2.7
- SQLite3 (default) / PostgreSQL

## Instalasi
1. Clone repositori:
   ```bash
   git clone https://github.com/username/Mbayar.git
   cd Mbayar