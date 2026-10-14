/**
 * COINTECA S.A.S. - Módulo de Recursos Humanos
 * nomina_lista.js - Control de modal para creación de nuevos períodos de nómina.
 */

function abrirModalNuevoPeriodo() {
    document.getElementById('modalNuevoPeriodo').classList.remove('hidden');
}
function cerrarModalNuevoPeriodo() {
    document.getElementById('modalNuevoPeriodo').classList.add('hidden');
}
function abrirModalImportar() {
    document.getElementById('modalImportar').classList.remove('hidden');
}
function cerrarModalImportar() {
    document.getElementById('modalImportar').classList.add('hidden');
}

document.addEventListener('DOMContentLoaded', function () {
    const input = document.getElementById('buscador-periodos-nomina');
    const btnLimpiar = document.getElementById('btn-limpiar-periodos');
    const filas = document.querySelectorAll('.fila-periodo-nomina');

    if (input) {
        input.addEventListener('input', function () {
            const q = this.value.toLowerCase().trim();
            if (btnLimpiar) btnLimpiar.classList.toggle('hidden', !q);
            let visibles = 0;
            filas.forEach(f => {
                const texto = f.textContent.toLowerCase();
                if (!q || texto.includes(q)) {
                    f.style.display = '';
                    visibles++;
                } else {
                    f.style.display = 'none';
                }
            });

            let filaVacia = document.getElementById('fila-sin-periodos-busqueda');
            const tbody = document.getElementById('tbody-periodos-nomina');
            if (visibles === 0 && filas.length > 0) {
                if (!filaVacia && tbody) {
                    filaVacia = document.createElement('tr');
                    filaVacia.id = 'fila-sin-periodos-busqueda';
                    filaVacia.innerHTML = `<td colspan="8" class="py-8 text-center text-slate-400 font-medium">No se encontraron períodos de pago que coincidan con "<strong>${q}</strong>".</td>`;
                    tbody.appendChild(filaVacia);
                }
            } else if (filaVacia) {
                filaVacia.remove();
            }
        });
    }

    window.limpiarBuscadorPeriodos = function () {
        if (input) {
            input.value = '';
            input.dispatchEvent(new Event('input'));
            input.focus();
        }
    };
});
