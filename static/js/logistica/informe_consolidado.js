/**
 * COINTECA S.A.S. - Módulo de Logística
 * informe_consolidado.js - Filtros en vivo de proyectos consolidados y exportaciones.
 */

function cambiarPestanaInforme(tabName) {
    const pConsolidado = document.getElementById('panelInformeConsolidado');
    const pDesglose = document.getElementById('panelInformeDesglose');
    const btnConsolidado = document.getElementById('tabBtnInformeConsolidado');
    const btnDesglose = document.getElementById('tabBtnInformeDesglose');

    if (tabName === 'consolidado') {
        if (pConsolidado) { pConsolidado.classList.remove('hidden'); pConsolidado.style.display = ''; }
        if (pDesglose) { pDesglose.classList.add('hidden'); pDesglose.style.display = 'none'; }
        if (btnConsolidado) { btnConsolidado.className = 'py-3 px-5 text-sm transition flex items-center gap-2 border-b-2 border-blue-600 text-primary font-bold tab-btn-informe'; }
        if (btnDesglose) { btnDesglose.className = 'py-3 px-5 text-sm transition flex items-center gap-2 text-muted-foreground hover:text-gray-700 tab-btn-informe'; }
    } else {
        if (pConsolidado) { pConsolidado.classList.add('hidden'); pConsolidado.style.display = 'none'; }
        if (pDesglose) { pDesglose.classList.remove('hidden'); pDesglose.style.display = ''; }
        if (btnConsolidado) { btnConsolidado.className = 'py-3 px-5 text-sm transition flex items-center gap-2 text-muted-foreground hover:text-gray-700 tab-btn-informe'; }
        if (btnDesglose) { btnDesglose.className = 'py-3 px-5 text-sm transition flex items-center gap-2 border-b-2 border-indigo-600 text-indigo-600 font-bold tab-btn-informe'; }
    }

    filtrarInformeActivo();
}

function filtrarInformeActivo() {
    const input = document.getElementById('buscadorInformeConsolidado');
    const btnLimpiar = document.getElementById('btnLimpiarInforme');
    const contador = document.getElementById('contadorInformeFiltrados');
    if (!input) return;

    const q = input.value.toLowerCase().trim();

    if (btnLimpiar) {
        if (q.length > 0) {
            btnLimpiar.classList.remove('hidden');
            btnLimpiar.classList.add('flex');
        } else {
            btnLimpiar.classList.add('hidden');
            btnLimpiar.classList.remove('flex');
        }
    }

    const pConsolidado = document.getElementById('panelInformeConsolidado');
    const esConsolidadoVisible = pConsolidado && !pConsolidado.classList.contains('hidden') && pConsolidado.style.display !== 'none';

    let selector = esConsolidadoVisible ? '.fila-informe-consolidado' : '.fila-informe-desglose';
    const filas = document.querySelectorAll(selector);
    let visibles = 0;

    filas.forEach(f => {
        const texto = f.textContent.toLowerCase();
        const match = (q === '' || texto.includes(q));
        f.style.display = match ? '' : 'none';
        if (match) visibles++;
    });

    if (contador) {
        if (q.length > 0) {
            contador.textContent = `${visibles} de ${filas.length} registros encontrados`;
        } else {
            contador.textContent = `Búsqueda rápida en la pestaña activa (${filas.length} registros)`;
        }
    }
}

document.addEventListener('DOMContentLoaded', function () {
    const inputBuscador = document.getElementById('buscadorInformeConsolidado');
    const btnLimpiar = document.getElementById('btnLimpiarInforme');

    if (inputBuscador) {
        inputBuscador.addEventListener('input', filtrarInformeActivo);
        inputBuscador.addEventListener('keydown', function (e) {
            if (e.key === 'Escape') {
                inputBuscador.value = '';
                filtrarInformeActivo();
            }
        });
    }

    if (btnLimpiar) {
        btnLimpiar.addEventListener('click', function () {
            if (inputBuscador) {
                inputBuscador.value = '';
                filtrarInformeActivo();
                inputBuscador.focus();
            }
        });
    }
});
