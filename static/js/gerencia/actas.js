/**
 * COINTECA S.A.S. - Módulo de Gerencia
 * actas.js - Búsqueda y filtros en vivo de actas de junta directiva por estado.
 */

document.addEventListener('DOMContentLoaded', function () {
    const inputBuscar = document.getElementById('buscarActa');
    const filtroEstado = document.getElementById('filtroEstado');
    const filas = document.querySelectorAll('.fila-acta');
    const contador = document.getElementById('contadorActas');

    function aplicarFiltros() {
        const query = (inputBuscar ? inputBuscar.value : '').toLowerCase().trim();
        const estadoSel = filtroEstado ? filtroEstado.value : 'todos';
        let visibles = 0;

        filas.forEach(fila => {
            const textoFila = fila.innerText.toLowerCase();
            const estadoFila = fila.getAttribute('data-estado') || '';

            const coincideTexto = !query || textoFila.includes(query);
            const coincideEstado = (estadoSel === 'todos') || (estadoFila === estadoSel);

            if (coincideTexto && coincideEstado) {
                fila.style.display = '';
                visibles++;
            } else {
                fila.style.display = 'none';
            }
        });

        if (contador) {
            contador.textContent = visibles;
        }
    }

    if (inputBuscar) inputBuscar.addEventListener('input', aplicarFiltros);
    if (filtroEstado) filtroEstado.addEventListener('change', aplicarFiltros);
});
