/**
 * COINTECA S.A.S. - Módulo de Logística
 * materiales_home.js - Control de pestañas de bodega (stock, historial, devoluciones), modales y buscadores en tiempo real.
 */

// Buscadores en tiempo real
    document.addEventListener('DOMContentLoaded', function () {
        // 1. Buscador de existencias (Stock)
        const inputBuscador = document.getElementById('buscadorMateriales');
        const btnLimpiarStock = document.getElementById('btnLimpiarStock');
        const contadorStock = document.getElementById('contadorStockVisible');
        const filasStock = document.querySelectorAll('.fila-inventario');

        function filtrarStock() {
            const query = inputBuscador ? inputBuscador.value.toLowerCase().trim() : '';
            if (btnLimpiarStock) {
                if (query.length > 0) {
                    btnLimpiarStock.classList.remove('hidden');
                    btnLimpiarStock.classList.add('flex');
                } else {
                    btnLimpiarStock.classList.add('hidden');
                    btnLimpiarStock.classList.remove('flex');
                }
            }

            let visibles = 0;
            filasStock.forEach(function (fila) {
                const texto = fila.textContent.toLowerCase();
                const match = (query === '' || texto.includes(query));
                fila.style.display = match ? '' : 'none';
                if (match) visibles++;
            });

            if (contadorStock) contadorStock.textContent = visibles;
        }

        if (inputBuscador) {
            inputBuscador.addEventListener('input', filtrarStock);
            inputBuscador.addEventListener('keydown', function(e) {
                if (e.key === 'Escape') {
                    inputBuscador.value = '';
                    filtrarStock();
                }
            });
        }
        if (btnLimpiarStock) {
            btnLimpiarStock.addEventListener('click', function() {
                if (inputBuscador) {
                    inputBuscador.value = '';
                    filtrarStock();
                    inputBuscador.focus();
                }
            });
        }

        // 2. Buscador de historial
        const inputHistorial = document.getElementById('buscadorHistorial');
        const btnLimpiarHistorial = document.getElementById('btnLimpiarHistorial');
        const contadorHistorial = document.getElementById('contadorHistorialVisible');
        const filasHistorial = document.querySelectorAll('.fila-historial');

        function filtrarHistorial() {
            const query = inputHistorial ? inputHistorial.value.toLowerCase().trim() : '';
            if (btnLimpiarHistorial) {
                if (query.length > 0) {
                    btnLimpiarHistorial.classList.remove('hidden');
                    btnLimpiarHistorial.classList.add('flex');
                } else {
                    btnLimpiarHistorial.classList.add('hidden');
                    btnLimpiarHistorial.classList.remove('flex');
                }
            }

            let visibles = 0;
            filasHistorial.forEach(function (fila) {
                const texto = fila.textContent.toLowerCase();
                const match = (query === '' || texto.includes(query));
                fila.style.display = match ? '' : 'none';
                if (match) visibles++;
            });

            if (contadorHistorial) contadorHistorial.textContent = visibles;
        }

        if (inputHistorial) {
            inputHistorial.addEventListener('input', filtrarHistorial);
            inputHistorial.addEventListener('keydown', function(e) {
                if (e.key === 'Escape') {
                    inputHistorial.value = '';
                    filtrarHistorial();
                }
            });
        }
        if (btnLimpiarHistorial) {
            btnLimpiarHistorial.addEventListener('click', function() {
                if (inputHistorial) {
                    inputHistorial.value = '';
                    filtrarHistorial();
                    inputHistorial.focus();
                }
            });
        }

        // 3. Buscador de devoluciones y retiros
        const inputDev = document.getElementById('buscadorDevoluciones');
        const btnLimpiarDev = document.getElementById('btnLimpiarDevoluciones');
        const contadorDev = document.getElementById('contadorDevolucionesVisible');
        const filasDev = document.querySelectorAll('.fila-retiro-bodega');

        function filtrarDevoluciones() {
            const query = inputDev ? inputDev.value.toLowerCase().trim() : '';
            if (btnLimpiarDev) {
                if (query.length > 0) {
                    btnLimpiarDev.classList.remove('hidden');
                    btnLimpiarDev.classList.add('flex');
                } else {
                    btnLimpiarDev.classList.add('hidden');
                    btnLimpiarDev.classList.remove('flex');
                }
            }

            let visibles = 0;
            filasDev.forEach(function (fila) {
                const texto = fila.textContent.toLowerCase();
                const match = (query === '' || texto.includes(query));
                fila.style.display = match ? '' : 'none';
                if (match) visibles++;
            });

            if (contadorDev) contadorDev.textContent = visibles;
        }

        if (inputDev) {
            inputDev.addEventListener('input', filtrarDevoluciones);
            inputDev.addEventListener('keydown', function(e) {
                if (e.key === 'Escape') {
                    inputDev.value = '';
                    filtrarDevoluciones();
                }
            });
        }
        if (btnLimpiarDev) {
            btnLimpiarDev.addEventListener('click', function() {
                if (inputDev) {
                    inputDev.value = '';
                    filtrarDevoluciones();
                    inputDev.focus();
                }
            });
        }

        // Detectar si la URL viene con ?tab=historial o ?tab=devoluciones
        const urlParams = new URLSearchParams(window.location.search);
        const tabParam = urlParams.get('tab');
        if (tabParam && ['stock', 'historial', 'devoluciones'].includes(tabParam)) {
            cambiarPestanaBodega(tabParam);
        }
    });

    // Modales
    function abrirModalAjuste(id, nombre, cantidad, unidad) {
        document.getElementById('modalMaterialId').value = id;
        document.getElementById('modalMaterialNombre').value = nombre;
        document.getElementById('modalMaterialCantidad').value = cantidad;
        const obsEl = document.getElementById('modalMaterialObservacion');
        if (obsEl) obsEl.value = '';
        let uVal = (unidad || '').toUpperCase();
        if (uVal === 'U') uVal = 'UN';
        document.getElementById('modalMaterialUnidad').value = (['M', 'MT', 'UN', 'KG', 'JGO'].includes(uVal)) ? uVal : 'UN';

        const modal = document.getElementById('modalAjusteStock');
        modal.classList.remove('hidden');
        modal.classList.add('flex');
    }

    function cerrarModalAjuste() {
        const modal = document.getElementById('modalAjusteStock');
        modal.classList.add('hidden');
        modal.classList.remove('flex');
    }

    function abrirModalNuevoMaterial() {
        const modal = document.getElementById('modalNuevoMaterial');
        modal.classList.remove('hidden');
        modal.classList.add('flex');
    }

    function cerrarModalNuevoMaterial() {
        const modal = document.getElementById('modalNuevoMaterial');
        if (!modal) return;
        modal.classList.add('hidden');
        modal.classList.remove('flex');
    }

    // Cerrar modales con tecla Escape o clic en el fondo oscuro
    document.addEventListener('keydown', function (e) {
        if (e.key === 'Escape') {
            cerrarModalAjuste();
            cerrarModalNuevoMaterial();
        }
    });
    ['modalAjusteStock', 'modalNuevoMaterial'].forEach(function (id) {
        const modal = document.getElementById(id);
        if (modal) {
            modal.addEventListener('click', function (e) {
                if (e.target === modal) {
                    if (id === 'modalAjusteStock') cerrarModalAjuste();
                    else cerrarModalNuevoMaterial();
                }
            });
        }
    });

    function cambiarPestanaBodega(tabName) {
        const panelStock = document.getElementById('panelStockBodega');
        const panelHistorial = document.getElementById('panelHistorialBodega');
        const panelDev = document.getElementById('panelDevolucionesBodega');

        const btnStock = document.getElementById('tabBtnStockBodega');
        const btnHistorial = document.getElementById('tabBtnHistorialBodega');
        const btnDev = document.getElementById('tabBtnDevolucionesBodega');

        // Ocultar todos los paneles
        if (panelStock) panelStock.classList.add('hidden');
        if (panelHistorial) panelHistorial.classList.add('hidden');
        if (panelDev) panelDev.classList.add('hidden');

        // Clases inactivas
        const inactivoCls = 'py-3 px-5 text-sm transition flex items-center gap-2 whitespace-nowrap text-muted-foreground hover:text-gray-700 tab-btn-bodega';
        if (btnStock) btnStock.className = inactivoCls;
        if (btnHistorial) btnHistorial.className = inactivoCls;
        if (btnDev) btnDev.className = inactivoCls;

        if (tabName === 'stock') {
            if (panelStock) panelStock.classList.remove('hidden');
            if (btnStock) btnStock.className = 'py-3 px-5 text-sm transition flex items-center gap-2 whitespace-nowrap border-b-2 border-primary text-primary font-bold tab-btn-bodega';
        } else if (tabName === 'historial') {
            if (panelHistorial) panelHistorial.classList.remove('hidden');
            if (btnHistorial) btnHistorial.className = 'py-3 px-5 text-sm transition flex items-center gap-2 whitespace-nowrap border-b-2 border-blue-600 text-blue-900 font-bold tab-btn-bodega';
        } else if (tabName === 'devoluciones') {
            if (panelDev) panelDev.classList.remove('hidden');
            if (btnDev) btnDev.className = 'py-3 px-5 text-sm transition flex items-center gap-2 whitespace-nowrap border-b-2 border-amber-600 text-amber-900 font-bold tab-btn-bodega';
        }
    }
