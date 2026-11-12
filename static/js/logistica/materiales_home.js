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

        // Listeners para validación en tiempo real de ítems duplicados
        const inputItemAjuste = document.getElementById('modalMaterialItem');
        if (inputItemAjuste) {
            inputItemAjuste.addEventListener('input', validarItemAjuste);
        }

        const inputItemNuevo = document.getElementById('campo-item');
        if (inputItemNuevo) {
            inputItemNuevo.addEventListener('input', validarItemNuevo);
        }

        const formAjuste = document.getElementById('formAjusteStock');
        if (formAjuste) {
            formAjuste.addEventListener('submit', function (e) {
                if (!validarItemAjuste()) {
                    e.preventDefault();
                }
            });
        }

        const formNuevo = document.getElementById('formNuevoMaterial');
        if (formNuevo) {
            formNuevo.addEventListener('submit', function (e) {
                if (!validarItemNuevo()) {
                    e.preventDefault();
                }
            });
        }
    });

    let materialIdActual = null;

    // Obtener catálogo actual de ítems para validación instantánea
    function obtenerCatalogoItems() {
        const mapa = {};
        document.querySelectorAll('.fila-inventario').forEach(function (fila) {
            const id = fila.getAttribute('data-material-id');
            const item = fila.getAttribute('data-material-item');
            const desc = fila.getAttribute('data-material-descripcion') || '';
            if (item) {
                mapa[String(item).trim()] = { id: id, descripcion: desc };
            }
        });
        return mapa;
    }

    function validarItemAjuste() {
        const input = document.getElementById('modalMaterialItem');
        const aviso = document.getElementById('avisoItemDuplicadoAjuste');
        const textoAviso = document.getElementById('textoAvisoItemDuplicadoAjuste');
        const btnGuardar = document.getElementById('btnGuardarAjuste');
        if (!input) return true;

        const val = input.value.trim();
        if (!val) {
            if (aviso) aviso.classList.add('hidden');
            input.classList.remove('border-red-500', 'focus:border-red-500');
            input.classList.add('border-gray-300');
            if (btnGuardar) btnGuardar.disabled = false;
            return true;
        }

        const catalogo = obtenerCatalogoItems();
        const existe = catalogo[val];

        if (existe && String(existe.id) !== String(materialIdActual)) {
            if (aviso) aviso.classList.remove('hidden');
            if (textoAviso) {
                textoAviso.textContent = `El número de ítem #${val} ya pertenece a "${existe.descripcion}". Elige otro número para evitar duplicados.`;
            }
            input.classList.add('border-red-500', 'focus:border-red-500');
            input.classList.remove('border-gray-300');
            if (btnGuardar) btnGuardar.disabled = true;
            return false;
        } else {
            if (aviso) aviso.classList.add('hidden');
            input.classList.remove('border-red-500', 'focus:border-red-500');
            input.classList.add('border-gray-300');
            if (btnGuardar) btnGuardar.disabled = false;
            return true;
        }
    }

    function validarItemNuevo() {
        const input = document.getElementById('campo-item');
        const aviso = document.getElementById('avisoItemDuplicadoNuevo');
        const textoAviso = document.getElementById('textoAvisoItemDuplicadoNuevo');
        const btnCrear = document.getElementById('btnCrearMaterial');
        if (!input) return true;

        const val = input.value.trim();
        if (!val) {
            if (aviso) aviso.classList.add('hidden');
            input.classList.remove('border-red-500', 'focus:border-red-500');
            input.classList.add('border-gray-300');
            if (btnCrear) btnCrear.disabled = false;
            return true;
        }

        const catalogo = obtenerCatalogoItems();
        const existe = catalogo[val];

        if (existe) {
            if (aviso) aviso.classList.remove('hidden');
            if (textoAviso) {
                textoAviso.textContent = `El número de ítem #${val} ya está registrado para "${existe.descripcion}". No se pueden duplicar números de ítem.`;
            }
            input.classList.add('border-red-500', 'focus:border-red-500');
            input.classList.remove('border-gray-300');
            if (btnCrear) btnCrear.disabled = true;
            return false;
        } else {
            if (aviso) aviso.classList.add('hidden');
            input.classList.remove('border-red-500', 'focus:border-red-500');
            input.classList.add('border-gray-300');
            if (btnCrear) btnCrear.disabled = false;
            return true;
        }
    }

    // Modales
    function abrirModalAjuste(id, item, nombre, cantidad, unidad) {
        materialIdActual = id;

        const idEl = document.getElementById('modalMaterialId');
        if (idEl) idEl.value = id;

        const itemEl = document.getElementById('modalMaterialItem');
        if (itemEl) itemEl.value = item || '';

        const nombreEl = document.getElementById('modalMaterialNombre');
        if (nombreEl) nombreEl.value = nombre || '';

        const cantEl = document.getElementById('modalMaterialCantidad');
        if (cantEl) cantEl.value = cantidad || '';

        const obsEl = document.getElementById('modalMaterialObservacion');
        if (obsEl) obsEl.value = '';

        let uVal = (unidad || '').toUpperCase();
        if (uVal === 'U') uVal = 'UN';
        const unidadEl = document.getElementById('modalMaterialUnidad');
        if (unidadEl) {
            unidadEl.value = (['M', 'MT', 'UN', 'KG', 'JGO'].includes(uVal)) ? uVal : 'UN';
        }

        validarItemAjuste();

        const modal = document.getElementById('modalAjusteStock');
        if (modal) {
            modal.classList.remove('hidden');
            modal.classList.add('flex');
        }
    }

    function cerrarModalAjuste() {
        const modal = document.getElementById('modalAjusteStock');
        if (modal) {
            modal.classList.add('hidden');
            modal.classList.remove('flex');
        }
        materialIdActual = null;
    }

    function abrirModalNuevoMaterial() {
        const itemInput = document.getElementById('campo-item');
        if (itemInput) itemInput.value = '';
        const descInput = document.getElementById('campo-descripcion');
        if (descInput) descInput.value = '';
        const cantInput = document.getElementById('campo-cantidad_inicial');
        if (cantInput) cantInput.value = '0';

        validarItemNuevo();

        const modal = document.getElementById('modalNuevoMaterial');
        if (modal) {
            modal.classList.remove('hidden');
            modal.classList.add('flex');
        }
    }

    function cerrarModalNuevoMaterial() {
        const modal = document.getElementById('modalNuevoMaterial');
        if (modal) {
            modal.classList.add('hidden');
            modal.classList.remove('flex');
        }
    }

    // Funciones para eliminar material con confirmación
    function confirmarEliminarMaterial(id, item, descripcion) {
        if (!id) return;
        const msg = `¿Estás seguro de que deseas eliminar permanentemente el material #${item || ''} "${descripcion}" del catálogo?\n\nEsta acción no se puede deshacer.`;
        if (confirm(msg)) {
            const form = document.getElementById('formEliminarMaterial');
            const inputId = document.getElementById('eliminarMaterialId');
            if (form && inputId) {
                inputId.value = id;
                form.submit();
            }
        }
    }

    function confirmarEliminarMaterialModal() {
        if (!materialIdActual) return;
        const nombreEl = document.getElementById('modalMaterialNombre');
        const itemEl = document.getElementById('modalMaterialItem');
        const desc = nombreEl ? nombreEl.value : 'Material';
        const item = itemEl ? itemEl.value : '';
        confirmarEliminarMaterial(materialIdActual, item, desc);
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
