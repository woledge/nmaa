/**
 * Barcode Price Display — Vanilla JS (no framework)
 *
 * Listens to window-level keydown events from barcode scanner.
 * Uses 200ms debounce to detect end of barcode (no Enter needed).
 * Fetches product info via JSON-RPC to /price-display/search.
 * Auto-clears result after 3 seconds.
 */

(function() {
    'use strict';

    let buffer = '';
    let debounceTimer = null;
    let clearTimer = null;
    let fullscreenRequested = false;

    const idleEl = document.getElementById('idle');
    const resultEl = document.getElementById('result');
    const notFoundEl = document.getElementById('not-found');
    const notFoundBarcodeEl = document.getElementById('not-found-barcode');

    function requestFullscreen() {
        if (fullscreenRequested) return;
        var el = document.documentElement;
        var fn = el.requestFullscreen || el.webkitRequestFullscreen || el.msRequestFullscreen;
        if (fn) {
            fn.call(el).catch(function() {});
            fullscreenRequested = true;
        }
    }

    // Tap/click anywhere to enter fullscreen (kiosk mode)
    document.addEventListener('click', requestFullscreen);
    document.addEventListener('touchstart', requestFullscreen);

    // Listen to ALL keydown on window (barcode scanner sends digits)
    window.addEventListener('keydown', function(ev) {
        requestFullscreen();
        // Only accept digits 0-9
        if (ev.key >= '0' && ev.key <= '9') {
            buffer += ev.key;
            // Cancel previous debounce
            if (debounceTimer) clearTimeout(debounceTimer);
            // Start new debounce — if no new digit in 200ms, search
            debounceTimer = setTimeout(search, 200);
        }
    });

    function search() {
        const barcode = buffer;
        buffer = '';

        if (barcode.length < 4) return;

        // Show loading
        showLoading();

        // JSON-RPC call to Odoo controller
        fetch('/price-display/search', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                jsonrpc: '2.0',
                method: 'call',
                params: { barcode: barcode },
                id: Date.now(),
            }),
        })
        .then(function(r) { return r.json(); })
        .then(function(data) {
            var result = data.result;
            if (result && result.found) {
                showProduct(result);
            } else {
                showNotFound(result ? result.barcode : barcode);
            }
        })
        .catch(function(err) {
            console.error('Search error:', err);
            showNotFound(barcode);
        });
    }

    function showLoading() {
        idleEl.classList.add('hidden');
        resultEl.classList.add('hidden');
        notFoundEl.classList.add('hidden');
        resultEl.innerHTML = '<div class="loading">⏳ Searching...</div>';
        resultEl.classList.remove('hidden');
    }

    function showProduct(data) {
        idleEl.classList.add('hidden');
        notFoundEl.classList.add('hidden');

        // Image or placeholder
        var imageHtml = '';
        if (data.image) {
            imageHtml = '<img src="' + data.image + '" class="product-image"/>';
        } else {
            imageHtml = '<div class="product-placeholder" style="background:' +
                data.placeholder_color + '">' +
                data.placeholder_letter + '</div>';
        }

        resultEl.innerHTML =
            '<div class="product-card">' +
                imageHtml +
                '<div class="product-name">' + escapeHtml(data.name) + '</div>' +
                '<div class="product-price">' +
                    data.price.toFixed(2) +
                    '<span class="product-currency">' + escapeHtml(data.currency) + '</span>' +
                '</div>' +
                '<div class="product-barcode">' + escapeHtml(data.barcode) + '</div>' +
            '</div>';
        resultEl.classList.remove('hidden');

        // Auto-clear after 3 seconds
        if (clearTimer) clearTimeout(clearTimer);
        clearTimer = setTimeout(clearAll, 5000);
    }

    function showNotFound(barcode) {
        idleEl.classList.add('hidden');
        resultEl.classList.add('hidden');
        notFoundBarcodeEl.textContent = barcode;
        notFoundEl.classList.remove('hidden');

        if (clearTimer) clearTimeout(clearTimer);
        clearTimer = setTimeout(clearAll, 5000);
    }

    function clearAll() {
        resultEl.classList.add('hidden');
        notFoundEl.classList.add('hidden');
        idleEl.classList.remove('hidden');
    }

    // Simple HTML escape to prevent XSS
    function escapeHtml(text) {
        if (!text) return '';
        var div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
})();
