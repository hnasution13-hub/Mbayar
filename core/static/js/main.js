/* ==================================================
 * FILE: main.js
 * PATH: core/static/js/main.js
 * FUNGSI: Utilitas utama untuk aplikasi Mbayar POS
 * FITUR:
 *   - Auto-hide alerts setelah 5 detik
 *   - Format Rupiah dan parsing
 *   - Loading spinner overlay
 *   - Konfirmasi dialog
 *   - Format tanggal dan waktu
 *   - Export ke CSV/Excel
 *   - Print receipt
 * VERSION: 1.0.0
 * UPDATE TERAKHIR: Initial implementation
 * ================================================== */

// ==================================================
// INITIALIZATION
// ==================================================
console.log('Mbayar POS siap digunakan!');

// Auto-hide alerts setelah 5 detik
document.addEventListener('DOMContentLoaded', function() {
    setTimeout(function() {
        document.querySelectorAll('.alert').forEach(function(alert) {
            let bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        });
    }, 5000);
});

// ==================================================
// FORMATTING FUNCTIONS
// ==================================================

/**
 * Format angka ke format Rupiah (contoh: Rp 1.000.000)
 * @param {number} angka - Angka yang akan diformat
 * @returns {string} String dalam format Rupiah
 */
function formatRupiah(angka) {
    return 'Rp ' + angka.toString().replace(/\B(?=(\d{3})+(?!\d))/g, '.');
}

/**
 * Parse string Rupiah ke number
 * @param {string} rupiah - String Rupiah (contoh: "Rp 1.000.000")
 * @returns {number} Nilai numerik
 */
function parseRupiah(rupiah) {
    return parseInt(rupiah.replace(/[^\d]/g, '')) || 0;
}

/**
 * Format tanggal ke format DD/MM/YYYY
 * @param {Date|string} date - Tanggal (Date object atau string)
 * @returns {string} Tanggal terformat
 */
function formatDate(date) {
    let d = new Date(date);
    return d.getDate().toString().padStart(2, '0') + '/' + 
           (d.getMonth() + 1).toString().padStart(2, '0') + '/' + 
           d.getFullYear();
}

/**
 * Format tanggal dan waktu ke format DD/MM/YYYY HH:MM
 * @param {Date|string} date - Tanggal (Date object atau string)
 * @returns {string} Datetime terformat
 */
function formatDateTime(date) {
    let d = new Date(date);
    return d.getDate().toString().padStart(2, '0') + '/' + 
           (d.getMonth() + 1).toString().padStart(2, '0') + '/' + 
           d.getFullYear() + ' ' + 
           d.getHours().toString().padStart(2, '0') + ':' + 
           d.getMinutes().toString().padStart(2, '0');
}

// ==================================================
// UI HELPER FUNCTIONS
// ==================================================

/**
 * Menampilkan loading spinner di tengah layar
 */
function showLoading() {
    let spinner = document.createElement('div');
    spinner.className = 'loading-spinner';
    spinner.innerHTML = '<div class="spinner-border text-primary" role="status"><span class="visually-hidden">Loading...</span></div>';
    document.body.appendChild(spinner);
}

/**
 * Menyembunyikan loading spinner
 */
function hideLoading() {
    let spinner = document.querySelector('.loading-spinner');
    if (spinner) spinner.remove();
}

/**
 * Menampilkan dialog konfirmasi dan menjalankan callback jika OK
 * @param {string} message - Pesan konfirmasi
 * @param {Function} callback - Fungsi yang dijalankan jika user mengkonfirmasi
 */
function confirmAction(message, callback) {
    if (confirm(message)) {
        callback();
    }
}

// ==================================================
// EXPORT & PRINT FUNCTIONS
// ==================================================

/**
 * Export data array ke file CSV
 * @param {Array<Array>} data - Array 2 dimensi berisi baris dan kolom
 * @param {string} filename - Nama file tanpa ekstensi
 */
function exportToExcel(data, filename) {
    let csv = '';
    data.forEach(row => {
        csv += row.join(',') + '\n';
    });
    
    let blob = new Blob([csv], { type: 'text/csv' });
    let url = window.URL.createObjectURL(blob);
    let a = document.createElement('a');
    a.href = url;
    a.download = filename + '.csv';
    a.click();
    
    // Bersihkan URL object
    window.URL.revokeObjectURL(url);
}

/**
 * Mencetak elemen HTML sebagai struk
 * @param {string} elementId - ID elemen yang akan dicetak
 */
function printReceipt(elementId) {
    let printContents = document.getElementById(elementId).innerHTML;
    let originalContents = document.body.innerHTML;
    
    document.body.innerHTML = printContents;
    window.print();
    document.body.innerHTML = originalContents;
    
    // Reload untuk mengembalikan event listener
    location.reload();
}