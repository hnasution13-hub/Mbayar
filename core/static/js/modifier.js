/* ==================================================
 * FILE: modifier.js
 * PATH: core/static/js/modifier.js
 * FUNGSI: Mengelola modal modifier untuk opsi tambahan menu di kasir
 * FITUR:
 *   - Menampilkan modal modifier dengan opsi (single, multiple, text)
 *   - Fetch data modifier dari server berdasarkan menu
 *   - Validasi required, min/max select
 *   - Menghitung total harga termasuk tambahan modifier
 *   - Menambahkan item dengan modifier ke keranjang
 * VERSION: 1.0.0
 * UPDATE TERAKHIR: Initial implementation
 * ================================================== */

// ==================================================
// MODIFIER MANAGER CLASS
// ==================================================
class ModifierManager {
    /**
     * Membuat instance ModifierManager
     * @param {Cashier} cashierInstance - Instance dari kelas Cashier utama
     */
    constructor(cashierInstance) {
        this.cashier = cashierInstance;
        this.currentMenu = null;
        this.currentModifiers = [];
        this.modifierModal = new bootstrap.Modal(document.getElementById('modifierModal'));
        this.init();
    }

    /* ==================== INITIALIZATION ==================== */
    init() {
        // Tombol konfirmasi di modal
        const confirmBtn = document.getElementById('confirmModifierBtn');
        if (confirmBtn) {
            confirmBtn.addEventListener('click', () => {
                this.confirmAddToCart();
            });
        }
    }

    /* ==================== PUBLIC METHODS ==================== */

    /**
     * Menampilkan modal modifier untuk menu tertentu
     * @param {string|number} menuId - ID menu
     * @param {string} menuName - Nama menu
     * @param {number} basePrice - Harga dasar menu
     * @param {boolean} isGofood - Apakah harga menggunakan GoFood
     */
    async showModifierModal(menuId, menuName, basePrice, isGofood = false) {
        try {
            this.showLoading();
            this.modifierModal.show();

            const data = await this.fetchModifiers(menuId);

            this.currentMenu = {
                id: menuId,
                name: menuName,
                basePrice: isGofood ? data.gofood_price : data.base_price,
                isGofood: isGofood,
                modifiers: data.modifiers
            };

            this.renderModifierModal();

        } catch (error) {
            console.error('Error loading modifiers:', error);
            this.modifierModal.hide();
            alert('Gagal memuat opsi menu. Menambahkan tanpa modifier.');

            // Fallback: tambah tanpa modifier
            this.cashier.addToCartDirect(menuId, menuName, basePrice, [], isGofood);
        }
    }

    /**
     * Mengonfirmasi pilihan modifier dan menambah ke keranjang
     */
    confirmAddToCart() {
        this.cashier.addToCartDirect(
            this.currentMenu.id,
            this.currentMenu.name,
            this.currentMenu.basePrice,
            this.currentModifiers,
            this.currentMenu.isGofood
        );
        this.modifierModal.hide();
    }

    /* ==================== PRIVATE METHODS ==================== */

    /**
     * Menampilkan spinner loading di modal
     */
    showLoading() {
        document.getElementById('modifierModalBody').innerHTML = `
            <div class="text-center py-5">
                <div class="spinner-border text-maroon" role="status"></div>
                <p class="mt-2">Memuat opsi...</p>
            </div>
        `;
    }

    /**
     * Fetch data modifier dari server
     * @param {string|number} menuId - ID menu
     * @returns {Promise<Object>} Data modifier
     */
    async fetchModifiers(menuId) {
        const response = await fetch(`/api/menu/${menuId}/modifiers/`);
        const data = await response.json();

        if (!data.success) {
            throw new Error(data.error || 'Gagal memuat modifier');
        }

        return data;
    }

    /**
     * Merender tampilan modal berdasarkan data modifier
     */
    renderModifierModal() {
        const modalBody = document.getElementById('modifierModalBody');
        const menu = this.currentMenu;

        document.getElementById('selectedMenuName').textContent = menu.name;

        if (!menu.modifiers || menu.modifiers.length === 0) {
            this.renderNoModifiers(modalBody);
            this.updateModalTotal();
            return;
        }

        let html = '';
        this.currentModifiers = [];

        menu.modifiers.forEach((modifier) => {
            html += this.renderModifierGroup(modifier);
        });

        modalBody.innerHTML = html;
        this.bindModifierEvents(modalBody);
        this.updateModalTotal();
    }

    /**
     * Merender pesan ketika tidak ada modifier
     * @param {HTMLElement} container - Elemen container
     */
    renderNoModifiers(container) {
        container.innerHTML = `
            <p class="text-muted text-center py-4">
                <i class="fas fa-info-circle fa-2x mb-3"></i><br>
                Tidak ada opsi tambahan untuk menu ini
            </p>
        `;
    }

    /**
     * Merender satu grup modifier (single, multiple, atau text)
     * @param {Object} modifier - Data modifier
     * @returns {string} HTML string
     */
    renderModifierGroup(modifier) {
        let html = `<div class="modifier-group mb-4 p-3 border rounded" data-modifier-id="${modifier.id}">`;
        html += `<h6 class="fw-bold mb-3">${modifier.name}`;
        if (modifier.required) {
            html += ` <span class="text-danger">*</span>`;
        }
        html += `</h6>`;

        if (modifier.type === 'text') {
            html += this.renderTextInput(modifier);
        } else {
            html += this.renderOptions(modifier);
        }

        html += `</div>`;
        return html;
    }

    /**
     * Merender input teks untuk modifier tipe text
     * @param {Object} modifier - Data modifier
     * @returns {string} HTML string
     */
    renderTextInput(modifier) {
        return `
            <textarea class="form-control modifier-input" 
                      data-modifier-id="${modifier.id}"
                      data-modifier-name="${modifier.name}"
                      placeholder="Tulis catatan di sini..."
                      rows="2"></textarea>
        `;
    }

    /**
     * Merender opsi radio/checkbox untuk modifier
     * @param {Object} modifier - Data modifier
     * @returns {string} HTML string
     */
    renderOptions(modifier) {
        let html = '';

        modifier.options.forEach(option => {
            const inputType = modifier.type === 'single' ? 'radio' : 'checkbox';
            const name = modifier.type === 'single' ? `modifier_${modifier.id}` : `modifier_${modifier.id}_${option.id}`;
            const isChecked = option.is_default ? 'checked' : '';

            html += `
                <div class="form-check mb-2 p-2 border-bottom">
                    <input class="form-check-input modifier-option" 
                           type="${inputType}" 
                           name="${name}"
                           data-modifier-id="${modifier.id}"
                           data-modifier-name="${modifier.name}"
                           data-option-id="${option.id}"
                           data-option-name="${option.name}"
                           data-price="${option.price_addition}"
                           ${isChecked}>
                    <label class="form-check-label w-100 d-flex justify-content-between">
                        <span>${option.name}</span>
                        ${option.price_addition > 0 ? 
                            `<span class="text-success fw-bold">+Rp ${option.price_addition.toLocaleString('id-ID')}</span>` : 
                            ''}
                    </label>
                </div>
            `;
        });

        return html;
    }

    /**
     * Menambahkan event listener ke elemen-elemen modifier
     * @param {HTMLElement} container - Container yang berisi elemen modifier
     */
    bindModifierEvents(container) {
        // Update total setiap ada perubahan
        container.querySelectorAll('.modifier-option, .modifier-input').forEach(input => {
            input.addEventListener('change', () => this.updateModalTotal());
            input.addEventListener('input', () => this.updateModalTotal());
        });

        // Untuk radio button, pastikan hanya satu yang bisa dipilih per group
        container.querySelectorAll('input[type="radio"]').forEach(radio => {
            radio.addEventListener('change', function() {
                const name = this.name;
                document.querySelectorAll(`input[name="${name}"]`).forEach(r => {
                    if (r !== this) r.checked = false;
                });
            });
        });
    }

    /**
     * Memperbarui total harga dan validasi di modal
     */
    updateModalTotal() {
        let additionalPrice = 0;
        const selectedModifiers = [];
        const errors = [];

        this.resetModalErrors();

        // Loop setiap modifier group
        document.querySelectorAll('.modifier-group').forEach(group => {
            const modifierId = group.dataset.modifierId;
            const modifier = this.currentMenu.modifiers.find(m => m.id == modifierId);
            if (!modifier) return;

            const selectedInGroup = this.getSelectedInGroup(group, modifier, additionalPrice);
            additionalPrice += selectedInGroup.additionalPrice;
            selectedModifiers.push(...selectedInGroup.items);

            this.validateGroup(modifier, selectedInGroup.items, errors, group);
        });

        this.currentModifiers = selectedModifiers;
        this.updateTotalPriceDisplay(additionalPrice);
        this.toggleConfirmButton(errors);
    }

    /**
     * Mereset tampilan error sebelumnya
     */
    resetModalErrors() {
        document.querySelectorAll('.modifier-group').forEach(g => {
            g.classList.remove('border-danger');
        });

        const existingError = document.getElementById('modifierErrors');
        if (existingError) existingError.remove();
    }

    /**
     * Mendapatkan item yang dipilih dalam satu grup
     * @param {HTMLElement} group - Elemen grup
     * @param {Object} modifier - Data modifier
     * @param {number} additionalPrice - Akumulator harga tambahan (pass by reference? tidak, kita kembalikan objek)
     * @returns {Object} Berisi items dan additionalPrice grup
     */
    getSelectedInGroup(group, modifier, additionalPriceAccum) {
        const items = [];
        let groupAdditional = 0;

        // Cek opsi yang dipilih
        group.querySelectorAll('.modifier-option:checked').forEach(option => {
            const price = parseFloat(option.dataset.price) || 0;
            groupAdditional += price;

            items.push({
                modifierId: modifier.id,
                modifierName: option.dataset.modifierName,
                optionId: option.dataset.optionId,
                optionName: option.dataset.optionName,
                price: price
            });
        });

        // Cek input teks
        group.querySelectorAll('.modifier-input').forEach(input => {
            if (input.value.trim()) {
                items.push({
                    modifierId: modifier.id,
                    modifierName: input.dataset.modifierName,
                    optionName: input.value.trim(),
                    price: 0,
                    isText: true
                });
            }
        });

        return { items, additionalPrice: groupAdditional };
    }

    /**
     * Validasi aturan required, min/max dalam satu grup
     * @param {Object} modifier - Data modifier
     * @param {Array} selectedItems - Item yang dipilih dalam grup
     * @param {Array} errors - Kumpulan error (dimodifikasi)
     * @param {HTMLElement} group - Elemen grup untuk styling
     */
    validateGroup(modifier, selectedItems, errors, group) {
        // Validasi required
        if (modifier.required && selectedItems.length === 0) {
            errors.push(`${modifier.name} wajib dipilih`);
            group.classList.add('border-danger');
        }

        // Validasi min/max untuk multiple
        if (modifier.type === 'multiple') {
            const count = selectedItems.length;
            if (modifier.min_select > 0 && count < modifier.min_select) {
                errors.push(`${modifier.name}: minimal pilih ${modifier.min_select}`);
                group.classList.add('border-danger');
            }
            if (modifier.max_select > 0 && count > modifier.max_select) {
                errors.push(`${modifier.name}: maksimal pilih ${modifier.max_select}`);
                group.classList.add('border-danger');
            }
        }
    }

    /**
     * Update tampilan total harga di modal
     * @param {number} additionalPrice - Total harga tambahan
     */
    updateTotalPriceDisplay(additionalPrice) {
        const total = this.currentMenu.basePrice + additionalPrice;
        document.getElementById('modalTotalPrice').textContent = 
            'Rp ' + Math.round(total).toLocaleString('id-ID');
    }

    /**
     * Mengaktifkan/menonaktifkan tombol konfirmasi berdasarkan error
     * @param {Array} errors - Daftar error
     */
    toggleConfirmButton(errors) {
        const confirmBtn = document.getElementById('confirmModifierBtn');

        if (errors.length > 0) {
            confirmBtn.disabled = true;
            this.showErrors(errors);
        } else {
            confirmBtn.disabled = false;
        }
    }

    /**
     * Menampilkan pesan error di modal
     * @param {Array} errors - Daftar error
     */
    showErrors(errors) {
        let errorHtml = '<div class="alert alert-danger mt-3" id="modifierErrors">';
        errors.forEach(e => { errorHtml += `<div>❌ ${e}</div>`; });
        errorHtml += '</div>';

        const modalBody = document.getElementById('modifierModalBody');
        let errorDiv = document.getElementById('modifierErrors');
        if (errorDiv) {
            errorDiv.innerHTML = errorHtml;
        } else {
            errorDiv = document.createElement('div');
            errorDiv.id = 'modifierErrors';
            errorDiv.innerHTML = errorHtml;
            modalBody.appendChild(errorDiv);
        }
    }
}

// ==================================================
// EXPORT (jika menggunakan module)
// ==================================================
// Jika menggunakan module system, bisa di-uncomment:
// export default ModifierManager;