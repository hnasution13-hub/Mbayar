/* ==================================================
 * FILE: chart.js
 * PATH: core/static/js/chart.js
 * FUNGSI: Manajemen grafik untuk dashboard menggunakan Chart.js
 * FITUR:
 *   - Membuat grafik line (penjualan harian)
 *   - Membuat grafik doughnut (kategori)
 *   - Membuat grafik bar (bulanan)
 *   - Menghancurkan chart yang tidak digunakan
 *   - Menyimpan instance chart untuk reuse
 * VERSION: 1.0.0
 * UPDATE TERAKHIR: Initial implementation
 * ================================================== */

// ==================================================
// CHART MANAGER CLASS
// ==================================================
class ChartManager {
    constructor() {
        // Menyimpan semua instance chart berdasarkan elementId
        this.charts = {};
    }

    /**
     * Membuat atau memperbarui grafik line penjualan
     * @param {string} elementId - ID elemen canvas
     * @param {Array} labels - Label sumbu X (misal: tanggal)
     * @param {Array} data - Data penjualan
     */
    createSalesChart(elementId, labels, data) {
        const ctx = document.getElementById(elementId)?.getContext('2d');
        if (!ctx) return;

        // Hancurkan chart lama jika ada
        this.destroyChart(elementId);

        this.charts[elementId] = new Chart(ctx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Penjualan',
                    data: data,
                    borderColor: '#667eea',
                    backgroundColor: 'rgba(102, 126, 234, 0.1)',
                    tension: 0.4,
                    fill: true
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            callback: function(value) {
                                return 'Rp ' + value.toLocaleString('id-ID');
                            }
                        }
                    }
                }
            }
        });
    }

    /**
     * Membuat atau memperbarui grafik doughnut kategori
     * @param {string} elementId - ID elemen canvas
     * @param {Array} labels - Label kategori
     * @param {Array} data - Data jumlah/penjualan per kategori
     */
    createCategoryChart(elementId, labels, data) {
        const ctx = document.getElementById(elementId)?.getContext('2d');
        if (!ctx) return;

        this.destroyChart(elementId);

        this.charts[elementId] = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: labels,
                datasets: [{
                    data: data,
                    backgroundColor: [
                        '#667eea',
                        '#764ba2',
                        '#84fab0',
                        '#f6d365',
                        '#fda085',
                        '#a1c4fd'
                    ]
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom'
                    }
                }
            }
        });
    }

    /**
     * Membuat atau memperbarui grafik bar bulanan
     * @param {string} elementId - ID elemen canvas
     * @param {Array} labels - Label bulan
     * @param {Array} data - Data penjualan per bulan
     */
    createMonthlyChart(elementId, labels, data) {
        const ctx = document.getElementById(elementId)?.getContext('2d');
        if (!ctx) return;

        this.destroyChart(elementId);

        this.charts[elementId] = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Penjualan',
                    data: data,
                    backgroundColor: '#667eea',
                    borderRadius: 5
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            callback: function(value) {
                                return 'Rp ' + value.toLocaleString('id-ID');
                            }
                        }
                    }
                }
            }
        });
    }

    /**
     * Menghancurkan chart berdasarkan elementId
     * @param {string} elementId - ID elemen canvas
     */
    destroyChart(elementId) {
        if (this.charts[elementId]) {
            this.charts[elementId].destroy();
            delete this.charts[elementId];
        }
    }
}

// ==================================================
// INITIALIZATION
// ==================================================
// Membuat instance global ChartManager
const chartManager = new ChartManager();