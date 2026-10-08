/**
 * COINTECA S.A.S. - Módulo de Contabilidad
 * caja_menor.js - Formateo dinámico de moneda en pesos colombianos para inputs de caja menor y movimientos.
 */

document.addEventListener("DOMContentLoaded", function () {
    const inputIds = ["campo-valor", "campo-valor_inicial"];
    inputIds.forEach(function (id) {
        const input = document.getElementById(id);
        if (input) {
            input.addEventListener("input", function (e) {
                const soloDigitos = e.target.value.replace(/\D/g, "");
                e.target.value = soloDigitos
                    ? new Intl.NumberFormat("es-CO").format(soloDigitos)
                    : "";
            });
        }
    });
});
