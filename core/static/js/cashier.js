/* ==================================================
 * FILE: cashier.js
 * PATH: core/static/js/cashier.js
 * FUNGSI: JavaScript utama untuk antarmuka Kasir POS
 * FITUR:
 *   - Manajemen Keranjang (add, remove, update quantity)
 *   - GoFood toggle dengan perubahan harga dinamis
 *   - Modifier Manager untuk opsi tambahan menu
 *   - Search dan filter kategori real-time
 *   - Kalkulasi subtotal, pajak, diskon, kembalian
 *   - Penyimpanan keranjang ke localStorage
 *   - Integrasi dengan Bootstrap Modal
 *   - Fetch API untuk ambil data modifier
 *   - Validasi input (required, min/max select)
 *   - Parsing Rupiah
 *   - Proses payment dengan CSRF Token
 *   - Responsive events
 * VERSION: 2.0.0
 * UPDATE TERAKHIR: Implementasi Modifier Manager & GoFood Toggle
 * ================================================== */

// ==================================================
// CASHIER CLASS - Main Controller
// ==================================================
class Cashier {
    constructor() {
        // Core properties
        this.cart = [];
        this.useGoFood = false;
        this.modifierManager = null;
        
        // Initialize
        this.init();
    }

    /* ==================== INITIALIZATION ==================== */
    init() {
        this.loadCartFromStorage();
        this.bindEvents();
        this.renderCart();
        
        // Inisialisasi modifier manager
        this.modifierManager = new ModifierManager(this);
    }

    /* ==================== EVENT BINDINGS ==================== */
    bindEvents() {
        this.bindMenuItems();
        this.bindOrderTypeToggle();
        this.bindSearch();
        this.bindCategoryFilter();
        this.bindDiscount();
        this.bindAmountPaid();
        this.bindPaymentMethod();
        this.bindProcessPayment();
    }

    bindMenuItems() {
        document.querySelectorAll('.menu-item').forEach(item => {
            item.addEventListener('click', (e) => {
                e.preventDefault();
                
                const id = item.dataset.id;
                const name = item.dataset.name;
                const price = this.useGoFood ? 
                    parseFloat(item.dataset.priceGofood) : 
                    parseFloat(item.dataset.price);
                const hasModifiers = item.dataset.hasModifiers === 'true';
                
                if (hasModifiers) {
                    this.modifierManager.showModifierModal(id, name, price, this.useGoFood);
                } else {
                    this.addToCartDirect(id, name, price, [], this.useGoFood);
                }
            });
        });
    }

    bindOrderTypeToggle() {
        document.querySelectorAll('input[name="orderType"]').forEach(radio => {
            radio.addEventListener('change', (e) => {
                this.useGoFood = e.target.value === 'gofood';
                this.updatePriceDisplay();
                this.updateCartPrices();
                this.renderCart();
            });
        });
    }

    bindSearch() {
        const searchInput = document.getElementById('searchMenu');
        if (searchInput) {
            searchInput.addEventListener('input', (e) => {
                this.searchMenu(e.target.value);
            });
        }
    }

    bindCategoryFilter() {
        document.querySelectorAll('.category-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                document.querySelectorAll('.category-btn').forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                this.filterByCategory(btn.dataset.category);
            });
        });
    }

    bindDiscount() {
        const discountInput = document.getElementById('discount');
        if (discountInput) {
            discountInput.addEventListener('input', () => this.updateTotals());
        }
    }

    bindAmountPaid() {
        const amountPaid = document.getElementById('amountPaid');
        if (amountPaid) {
            amountPaid.addEventListener('input', () => this.updateChange());
        }
    }

    bindPaymentMethod() {
        const paymentMethod = document.getElementById('paymentMethod');
        if (paymentMethod) {
            paymentMethod.addEventListener('change', () => this.handlePaymentMethodChange());
        }
    }

    bindProcessPayment() {
        const processBtn = document.getElementById('processPayment');
        if (processBtn) {
            processBtn.addEventListener('click', () => this.processPayment());
        }
    }

    /* ==================== UI UPDATE METHODS ==================== */
    updatePriceDisplay() {
        document.querySelectorAll('.menu-item').forEach(item => {
            const normalPrice = item.querySelector('.price-normal');
            const gofoodPrice = item.querySelector('.price-gofood');
            
            if (normalPrice && gofoodPrice) {
                if (this.useGoFood) {
                    normalPrice.style.display = 'none';
                    gofoodPrice.style.display = 'block';
                } else {
                    normalPrice.style.display = 'block';
                    gofoodPrice.style.display = 'none';
                }
            }
        });
    }

    updateCartPrices() {
        this.cart = this.cart.map(item => {
            const menuItem = document.querySelector(`.menu-item[data-id="${item.id}"]`);
            if (menuItem) {
                const newPrice = this.useGoFood ? 
                    parseFloat(menuItem.dataset.priceGofood) : 
                    parseFloat(menuItem.dataset.price);
                
                // Hitung ulang total price dengan modifier
                let totalPrice = newPrice;
                item.modifiers.forEach(mod => {
                    totalPrice += mod.price || 0;
                });
                
                return {
                    ...item,
                    basePrice: newPrice,
                    totalPrice: totalPrice,
                    isGofood: this.useGoFood
                };
            }
            return item;
        });
    }

    handlePaymentMethodChange() {
        const paymentMethod = document.getElementById('paymentMethod');
        const amountPaid = document.getElementById('amountPaid');
        
        if (paymentMethod.value === 'cash') {
            amountPaid.disabled = false;
        } else {
            amountPaid.disabled = true;
            amountPaid.value = this.parseRupiah(document.getElementById('total').textContent);
            this.updateChange();
        }
    }

    /* ==================== CART OPERATIONS ==================== */
    addToCartDirect(id, name, basePrice, modifiers, isGofood) {
        // Hitung total harga dengan modifier
        let totalPrice = basePrice;
        modifiers.forEach(mod => {
            totalPrice += mod.price || 0;
        });
        
        // Cek apakah item yang sama dengan modifier yang sama sudah ada
        const existingIndex = this.cart.findIndex(item => 
            item.id === id && 
            JSON.stringify(item.modifiers) === JSON.stringify(modifiers) &&
            item.isGofood === isGofood
        );
        
        if (existingIndex >= 0) {
            this.cart[existingIndex].quantity += 1;
        } else {
            this.cart.push({
                id: id,
                name: name,
                basePrice: basePrice,
                totalPrice: totalPrice,
                modifiers: modifiers || [],
                quantity: 1,
                isGofood: isGofood
            });
        }
        
        this.saveCartToStorage();
        this.renderCart();
    }

    addToCart(id, name, price) {
        this.addToCartDirect(id, name, price, [], this.useGoFood);
    }

    removeFromCart(id) {
        this.cart = this.cart.filter(item => item.id !== id);
        this.saveCartToStorage();
        this.renderCart();
    }

    updateQuantity(id, change) {
        const item = this.cart.find(item => item.id === id);
        if (item) {
            item.quantity += change;
            if (item.quantity <= 0) {
                this.removeFromCart(id);
            } else {
                this.saveCartToStorage();
                this.renderCart();
            }
        }
    }

    clearCart() {
        this.cart = [];
        localStorage.removeItem('mbayar_cart');
        this.renderCart();
    }

    /* ==================== RENDER METHODS ==================== */
    renderCart() {
        const cartContainer = document.getElementById('cartItems');
        if (!cartContainer) return;

        if (this.cart.length === 0) {
            this.renderEmptyCart(cartContainer);
        } else {
            this.renderCartItems(cartContainer);
        }
        
        this.updateTotals();
    }

    renderEmptyCart(container) {
        container.innerHTML = `
            <div class="empty-cart">
                <i class="fas fa-shopping-cart"></i>
                <p>Keranjang masih kosong</p>
                <small>Klik menu untuk menambah</small>
            </div>
        `;
        document.getElementById('processPayment').disabled = true;
    }

    renderCartItems(container) {
        let html = '';
        
        this.cart.forEach((item) => {
            const itemTotal = item.totalPrice * item.quantity;
            const gofoodBadge = item.isGofood ? '<span class="badge-gofood">GoFood</span>' : '';
            
            html += this.renderCartItem(item, gofoodBadge, itemTotal);
        });
        
        container.innerHTML = html;
        document.getElementById('processPayment').disabled = false;
    }

    renderCartItem(item, gofoodBadge, itemTotal) {
        return `
            <div class="cart-item">
                <div class="cart-item-info">
                    <div class="cart-item-title">
                        ${item.name} ${gofoodBadge}
                    </div>
                    ${this.renderModifierText(item.modifiers)}
                    <div class="cart-item-price">
                        Rp ${itemTotal.toLocaleString('id-ID')}
                        <small class="text-muted d-block">@ Rp ${item.totalPrice.toLocaleString('id-ID')}</small>
                    </div>
                </div>
                <div class="cart-item-actions">
                    <button class="qty-btn" onclick="cashier.updateQuantity('${item.id}', -1)">−</button>
                    <span class="qty-value">${item.quantity}</span>
                    <button class="qty-btn" onclick="cashier.updateQuantity('${item.id}', 1)">+</button>
                    <button class="qty-btn remove" onclick="cashier.removeFromCart('${item.id}')">×</button>
                </div>
            </div>
        `;
    }

    renderModifierText(modifiers) {
        if (!modifiers || modifiers.length === 0) return '';
        
        let text = '<small class="text-muted d-block" style="font-size: 0.75rem;">';
        text += modifiers.map(m => {
            if (m.price > 0) {
                return `${m.optionName} (+Rp ${m.price.toLocaleString('id-ID')})`;
            }
            return m.optionName;
        }).join(', ');
        text += '</small>';
        
        return text;
    }

    /* ==================== CALCULATION METHODS ==================== */
    updateTotals() {
        const subtotal = this.cart.reduce((sum, item) => sum + (item.totalPrice * item.quantity), 0);
        const discount = parseFloat(document.getElementById('discount')?.value) || 0;
        const tax = subtotal * 0.1;
        const total = subtotal - discount + tax;

        document.getElementById('subtotal').textContent = 'Rp ' + subtotal.toLocaleString('id-ID');
        document.getElementById('tax').textContent = 'Rp ' + tax.toLocaleString('id-ID');
        document.getElementById('total').textContent = 'Rp ' + total.toLocaleString('id-ID');
        
        this.updateChange();
    }

    updateChange() {
        const total = this.parseRupiah(document.getElementById('total').textContent);
        const amountPaid = parseFloat(document.getElementById('amountPaid')?.value) || 0;
        const change = amountPaid - total;
        
        document.getElementById('change').value = 'Rp ' + change.toLocaleString('id-ID');
        
        this.validatePayment(total, amountPaid);
    }

    validatePayment(total, amountPaid) {
        const paymentMethod = document.getElementById('paymentMethod')?.value;
        
        if (paymentMethod === 'cash' && amountPaid < total) {
            document.getElementById('processPayment').disabled = true;
        } else {
            document.getElementById('processPayment').disabled = this.cart.length === 0;
        }
    }

    /* ==================== FILTER METHODS ==================== */
    searchMenu(query) {
        query = query.toLowerCase();
        document.querySelectorAll('.menu-item').forEach(item => {
            const name = item.dataset.name.toLowerCase();
            item.style.display = name.includes(query) ? '' : 'none';
        });
    }

    filterByCategory(categoryId) {
        document.querySelectorAll('.menu-item').forEach(item => {
            const show = categoryId === 'all' || item.dataset.category === categoryId;
            item.style.display = show ? '' : 'none';
        });
    }

    /* ==================== STORAGE METHODS ==================== */
    saveCartToStorage() {
        localStorage.setItem('mbayar_cart', JSON.stringify(this.cart));
    }

    loadCartFromStorage() {
        const saved = localStorage.getItem('mbayar_cart');
        if (saved) {
            try {
                this.cart = JSON.parse(saved);
                // Pastikan setiap item punya field modifiers
                this.cart = this.cart.map(item => ({
                    ...item,
                    modifiers: item.modifiers || [],
                    basePrice: item.basePrice || item.price,
                    totalPrice: item.totalPrice || item.price
                }));
            } catch (e) {
                this.cart = [];
            }
        }
    }

    /* ==================== UTILITY METHODS ==================== */
    parseRupiah(rupiah) {
        return parseInt(rupiah.replace(/[^\d]/g, '')) || 0;
    }

    getCSRFToken() {
        return document.querySelector('[name=csrfmiddlewaretoken]')?.value || '';
    }

    /* ==================== PAYMENT PROCESSING ==================== */
    async processPayment() {
        const orderData = this.buildOrderData();
        
        try {
            const response = await fetch('/cashier/create-order/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                },
                body: JSON.stringify(orderData)
            });

            const data = await response.json();
            
            if (data.success) {
                this.clearCart();
                window.location.href = `/cashier/print/${data.order_no}/`;
            } else {
                alert('Terjadi kesalahan: ' + (data.error || 'Unknown error'));
            }
        } catch (error) {
            console.error('Error:', error);
            alert('Terjadi kesalahan jaringan');
        }
    }

    buildOrderData() {
        return {
            customer_name: document.getElementById('customerName')?.value || 'Umum',
            items: this.cart.map(item => ({
                menu_id: item.id,
                quantity: item.quantity,
                notes: '',
                is_gofood: item.isGofood,
                modifiers: item.modifiers || []
            })),
            payment_method: document.getElementById('paymentMethod')?.value,
            amount_paid: parseFloat(document.getElementById('amountPaid')?.value) || 0,
            discount: parseFloat(document.getElementById('discount')?.value) || 0,
            tax: this.parseRupiah(document.getElementById('tax')?.textContent),
            order_type: this.useGoFood ? 'gofood' : 'normal'
        };
    }
}

// ==================================================
// MODIFIER MANAGER CLASS
// ==================================================
class ModifierManager {
    constructor(cashierInstance) {
        this.cashier = cashierInstance;
        this.currentMenu = null;
        this.currentModifiers = [];
        this.modifierModal = null;
        this.init();
    }

    /* ==================== INITIALIZATION ==================== */
    init() {
        const modalElement = document.getElementById('modifierModal');
        if (modalElement) {
            this.modifierModal = new bootstrap.Modal(modalElement);
            
            document.getElementById('confirmModifierBtn')?.addEventListener('click', () => {
                this.confirmAddToCart();
            });
        }
    }

    /* ==================== MODAL HANDLING ==================== */
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
            this.handleModifierError(menuId, menuName, basePrice, isGofood);
        }
    }

    showLoading() {
        document.getElementById('modifierModalBody').innerHTML = `
            <div class="text-center py-5">
                <div class="spinner-border" style="color: #8B1E2D;" role="status"></div>
                <p class="mt-2">Memuat opsi...</p>
            </div>
        `;
    }

    async fetchModifiers(menuId) {
        const response = await fetch(`/api/menu/${menuId}/modifiers/`);
        const data = await response.json();
        
        if (!data.success) {
            throw new Error(data.error || 'Gagal memuat modifier');
        }
        
        return data;
    }

    handleModifierError(menuId, menuName, basePrice, isGofood) {
        console.error('Error loading modifiers:');
        this.modifierModal.hide();
        alert('Gagal memuat opsi menu. Menambahkan tanpa modifier.');
        this.cashier.addToCartDirect(menuId, menuName, basePrice, [], isGofood);
    }

    /* ==================== RENDER MODIFIER ==================== */
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

    renderNoModifiers(container) {
        container.innerHTML = `
            <p class="text-muted text-center py-4">
                <i class="fas fa-info-circle fa-2x mb-3"></i><br>
                Tidak ada opsi tambahan untuk menu ini
            </p>
        `;
    }

    renderModifierGroup(modifier) {
        let html = `
            <div class="modifier-group mb-4 p-3 border rounded" data-modifier-id="${modifier.id}">
                <h6 class="fw-bold mb-3">${modifier.name}
                    ${modifier.required ? '<span class="text-danger">*</span>' : ''}
                </h6>
        `;
        
        if (modifier.type === 'text') {
            html += this.renderTextInput(modifier);
        } else {
            html += this.renderOptions(modifier);
        }
        
        html += `</div>`;
        return html;
    }

    renderTextInput(modifier) {
        return `
            <textarea class="form-control modifier-input" 
                      data-modifier-id="${modifier.id}"
                      data-modifier-name="${modifier.name}"
                      placeholder="Tulis catatan di sini..."
                      rows="2"></textarea>
        `;
    }

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
                    <label class="form-check-label w-100 d-flex justify-content-between align-items-center">
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

    /* ==================== MODIFIER EVENTS ==================== */
    bindModifierEvents(container) {
        // Event listeners untuk update total
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

    /* ==================== MODAL CALCULATIONS ==================== */
    updateModalTotal() {
        let additionalPrice = 0;
        const selectedModifiers = [];
        const errors = [];
        
        this.resetModalState();
        
        // Loop setiap modifier group
        document.querySelectorAll('.modifier-group').forEach(group => {
            this.processModifierGroup(group, selectedModifiers, additionalPrice, errors);
        });
        
        this.currentModifiers = selectedModifiers;
        this.updateModalPrice(additionalPrice);
        this.validateSelection(errors);
    }

    resetModalState() {
        document.querySelectorAll('.modifier-group').forEach(g => {
            g.classList.remove('border-danger');
        });
        
        const existingError = document.getElementById('modifierErrors');
        if (existingError) existingError.remove();
    }

    processModifierGroup(group, selectedModifiers, additionalPrice, errors) {
        const modifierId = group.dataset.modifierId;
        const modifier = this.currentMenu.modifiers.find(m => m.id == modifierId);
        if (!modifier) return;
        
        const selectedInGroup = [];
        
        // Cek opsi yang dipilih
        group.querySelectorAll('.modifier-option:checked').forEach(option => {
            const price = parseFloat(option.dataset.price) || 0;
            additionalPrice += price;
            
            selectedInGroup.push({
                modifierId: modifierId,
                modifierName: option.dataset.modifierName,
                optionId: option.dataset.optionId,
                optionName: option.dataset.optionName,
                price: price
            });
        });
        
        // Cek input teks
        group.querySelectorAll('.modifier-input').forEach(input => {
            if (input.value.trim()) {
                selectedInGroup.push({
                    modifierId: modifierId,
                    modifierName: input.dataset.modifierName,
                    optionName: input.value.trim(),
                    price: 0,
                    isText: true
                });
            }
        });
        
        this.validateModifierGroup(modifier, selectedInGroup, errors, group);
        selectedModifiers.push(...selectedInGroup);
    }

    validateModifierGroup(modifier, selectedInGroup, errors, group) {
        // Validasi required
        if (modifier.required && selectedInGroup.length === 0) {
            errors.push(`${modifier.name} wajib dipilih`);
            group.classList.add('border-danger');
        }
        
        // Validasi min/max untuk multiple
        if (modifier.type === 'multiple') {
            const count = selectedInGroup.length;
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

    updateModalPrice(additionalPrice) {
        const total = this.currentMenu.basePrice + additionalPrice;
        document.getElementById('modalTotalPrice').textContent = 
            'Rp ' + Math.round(total).toLocaleString('id-ID');
    }

    validateSelection(errors) {
        const confirmBtn = document.getElementById('confirmModifierBtn');
        
        if (errors.length > 0) {
            confirmBtn.disabled = true;
            this.showErrors(errors);
        } else {
            confirmBtn.disabled = false;
        }
    }

    showErrors(errors) {
        let errorHtml = '<div class="alert alert-danger mt-3" id="modifierErrors">';
        errors.forEach(e => { 
            errorHtml += `<div><i class="fas fa-exclamation-circle me-1"></i> ${e}</div>`; 
        });
        errorHtml += '</div>';
        
        document.getElementById('modifierModalBody').appendChild(
            document.createRange().createContextualFragment(errorHtml)
        );
    }

    /* ==================== CONFIRMATION ==================== */
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
}

// ==================================================
// INITIALIZATION
// ==================================================
let cashier;

document.addEventListener('DOMContentLoaded', () => {
    // Pastikan bootstrap tersedia
    if (typeof bootstrap === 'undefined') {
        console.error('Bootstrap JS tidak ditemukan!');
        return;
    }
    
    cashier = new Cashier();
});