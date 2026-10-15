/**
 * COINTECA S.A.S. - Módulo de Logística
 * informe_consolidado.js - Filtros en vivo de proyectos consolidados y exportaciones.
 */

function cambiarPestanaInforme(tabName) {
    const pConsolidado = document.getElementById('panelInformeConsolidado');
    const pRequeridos = document.getElementById('panelInformeRequeridos');
    const pDesglose = document.getElementById('panelInformeDesglose');
    const btnConsolidado = document.getElementById('tabBtnInformeConsolidado');
    const btnRequeridos = document.getElementById('tabBtnInformeRequeridos');
    const btnDesglose = document.getElementById('tabBtnInformeDesglose');

    // Ocultar todos
    if (pConsolidado) { pConsolidado.classList.add('hidden'); pConsolidado.style.display = 'none'; }
    if (pRequeridos) { pRequeridos.classList.add('hidden'); pRequeridos.style.display = 'none'; }
    if (pDesglose) { pDesglose.classList.add('hidden'); pDesglose.style.display = 'none'; }

    // Clases por defecto (inactivo)
    const inactiveClass = 'py-3 px-5 text-sm transition flex items-center gap-2 text-muted-foreground hover:text-gray-700 tab-btn-informe';
    if (btnConsolidado) btnConsolidado.className = inactiveClass;
    if (btnRequeridos) btnRequeridos.className = inactiveClass;
    if (btnDesglose) btnDesglose.className = inactiveClass;

    if (tabName === 'requeridos') {
        if (pRequeridos) { pRequeridos.classList.remove('hidden'); pRequeridos.style.display = ''; }
        if (btnRequeridos) { btnRequeridos.className = 'py-3 px-5 text-sm transition flex items-center gap-2 border-b-2 border-emerald-600 text-emerald-800 font-bold tab-btn-informe'; }
    } else if (tabName === 'desglose') {
        if (pDesglose) { pDesglose.classList.remove('hidden'); pDesglose.style.display = ''; }
        if (btnDesglose) { btnDesglose.className = 'py-3 px-5 text-sm transition flex items-center gap-2 border-b-2 border-indigo-600 text-indigo-600 font-bold tab-btn-informe'; }
    } else {
        if (pConsolidado) { pConsolidado.classList.remove('hidden'); pConsolidado.style.display = ''; }
        if (btnConsolidado) { btnConsolidado.className = 'py-3 px-5 text-sm transition flex items-center gap-2 border-b-2 border-blue-600 text-primary font-bold tab-btn-informe'; }
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
    const pRequeridos = document.getElementById('panelInformeRequeridos');
    const esConsolidadoVisible = pConsolidado && !pConsolidado.classList.contains('hidden') && pConsolidado.style.display !== 'none';
    const esRequeridosVisible = pRequeridos && !pRequeridos.classList.contains('hidden') && pRequeridos.style.display !== 'none';

    let selector = '.fila-informe-desglose';
    if (esConsolidadoVisible) {
        selector = '.fila-informe-consolidado';
    } else if (esRequeridosVisible) {
        selector = '.fila-informe-requeridos';
    }

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

    const urlParams = new URLSearchParams(window.location.search);
    const tabParam = urlParams.get('tab');
    if (tabParam === 'requeridos') {
        cambiarPestanaInforme('requeridos');
    } else if (tabParam === 'desglose') {
        cambiarPestanaInforme('desglose');
    }
});
