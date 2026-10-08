/**
 * COINTECA S.A.S. - Módulo de Logística
 * crear_consumo.js - Validación dinámica de cantidades de consumo en proyectos.
 */

document.addEventListener('DOMContentLoaded', function () {
        // Poner fecha de hoy por defecto
        const inputFecha = document.getElementById('campoFechaReporte');
        if (inputFecha && !inputFecha.value) {
            const hoy = new Date().toISOString().split('T')[0];
            inputFecha.value = hoy;
        }

        const tbody = document.getElementById('filasConsumoMateriales');
        const btnAgregar = document.getElementById('btnAgregarFilaConsumo');

        btnAgregar.addEventListener('click', function () {
            const primeraFila = tbody.querySelector('.fila-material-consumo');
            if (primeraFila) {
                const nuevaFila = primeraFila.cloneNode(true);
                // Limpiar valores
                const select = nuevaFila.querySelector('select');
                if (select) select.selectedIndex = 0;
                const inputCant = nuevaFila.querySelector('input[type="number"]');
                if (inputCant) inputCant.value = '';
                tbody.appendChild(nuevaFila);
            }
        });

        tbody.addEventListener('click', function (e) {
            if (e.target.classList.contains('btnEliminarFilaConsumo')) {
                const filas = tbody.querySelectorAll('.fila-material-consumo');
                if (filas.length > 1) {
                    e.target.closest('.fila-material-consumo').remove();
                } else {
                    alert('Debe registrar al menos un material en el reporte de consumo.');
                }
            }
        });
    });
