// script.js — Auto EDA Analytics Dashboard
// Semua logika JavaScript utama ada di index.html <script> tag
// File ini untuk fungsi tambahan atau utility

// Utility: format angka Indonesia
function formatIDR(num) {
    return new Intl.NumberFormat('id-ID').format(num);
}

// Utility: format persentase
function formatPct(num) {
    return `${parseFloat(num).toFixed(2)}%`;
}

console.log("Analytics Dashboard — SD-1306 Kelompok 6 Kelas B");