/**
 * COINTECA S.A.S. - Módulo de Logística
 * detalle_proyecto.js - Control de pestañas, buscador en vivo y filtros interactivos de tabla tipo Excel.
 */

// ---------- CONTROL DE PESTAÑAS ----------
function cambiarPestanaDetalle(tabName) {
    cerrarFiltroExcel();

    const paneles = {
        'balance': document.getElementById('panelDetalleBalance'),
        'devoluciones': document.getElementById('panelDetalleDevoluciones'),
        'requeridos': document.getElementById('panelDetalleRequeridos'),
        'instalados': document.getElementById('panelDetalleInstalados'),
        'retiros': document.getElementById('panelDetalleRetiros'),
        'entradas': document.getElementById('panelDetalleEntradas')
    };

    const botones = {
        'balance': document.getElementById('tabBtnDetalleBalance'),
        'devoluciones': document.getElementById('tabBtnDetalleDevoluciones'),
        'requeridos': document.getElementById('tabBtnDetalleRequeridos'),
        'instalados': document.getElementById('tabBtnDetalleInstalados'),
        'retiros': document.getElementById('tabBtnDetalleRetiros'),
        'entradas': document.getElementById('tabBtnDetalleEntradas')
    };

    for (const key in paneles) {
        if (paneles[key]) {
            if (key === tabName) {
                paneles[key].classList.remove('hidden');
                paneles[key].style.display = '';
            } else {
                paneles[key].classList.add('hidden');
                paneles[key].style.display = 'none';
            }
        }
    }

    const activeClasses = {
        'balance': 'py-3 px-5 text-sm transition flex items-center gap-2 whitespace-nowrap border-b-2 border-blue-600 text-primary font-bold tab-btn-detalle',
        'devoluciones': 'py-3 px-5 text-sm transition flex items-center gap-2 whitespace-nowrap border-b-2 border-amber-600 text-amber-800 font-bold tab-btn-detalle',
        'requeridos': 'py-3 px-5 text-sm transition flex items-center gap-2 whitespace-nowrap border-b-2 border-blue-600 text-blue-700 font-bold tab-btn-detalle',
        'instalados': 'py-3 px-5 text-sm transition flex items-center gap-2 whitespace-nowrap border-b-2 border-indigo-600 text-indigo-700 font-bold tab-btn-detalle',
        'retiros': 'py-3 px-5 text-sm transition flex items-center gap-2 whitespace-nowrap border-b-2 border-amber-600 text-amber-800 font-bold tab-btn-detalle',
        'entradas': 'py-3 px-5 text-sm transition flex items-center gap-2 whitespace-nowrap border-b-2 border-emerald-600 text-emerald-600 font-bold tab-btn-detalle'
    };

    for (const key in botones) {
        if (botones[key]) {
            if (key === tabName) {
                botones[key].className = activeClasses[key] || 'py-3 px-5 text-sm transition flex items-center gap-2 whitespace-nowrap border-b-2 border-primary text-primary font-bold tab-btn-detalle';
            } else {
                botones[key].className = 'py-3 px-5 text-sm transition flex items-center gap-2 whitespace-nowrap text-muted-foreground hover:text-gray-700 tab-btn-detalle';
            }
        }
    }

    filtrarMaterialesActivos();
}

// ---------- BUSCADOR EN VIVO DE MATERIALES POR PESTAÑA ----------
function filtrarMaterialesActivos() {
    const input = document.getElementById("buscadorMaterialesProyecto");
    const btnLimpiar = document.getElementById("btnLimpiarBuscadorMat");
    const contador = document.getElementById("contadorMaterialesFiltrados");
    if (!input) return;

    const q = input.value.toLowerCase().trim();

    if (btnLimpiar) {
        if (q.length > 0) {
            btnLimpiar.classList.remove("hidden");
            btnLimpiar.classList.add("flex");
        } else {
            btnLimpiar.classList.add("hidden");
            btnLimpiar.classList.remove("flex");
        }
    }

    const panelActivo = document.querySelector(".pestana-panel-detalle:not(.hidden)");
    if (!panelActivo) return;

    const filas = Array.from(panelActivo.querySelectorAll("tbody tr:not(.fila-vacia):not(.fila-no-filtro)"));
    let visibles = 0;

    filas.forEach(f => {
        const texto = f.textContent.toLowerCase();
        const coincideBuscador = (q === "" || texto.includes(q));
        const ocultoPorExcel = f.dataset.ocultoPorExcel === "true";

        if (coincideBuscador && !ocultoPorExcel) {
            f.style.display = "";
            visibles++;
        } else {
            f.style.display = "none";
        }
    });

    if (contador) {
        if (q.length > 0) {
            contador.textContent = `${visibles} de ${filas.length} registros encontrados`;
        } else {
            contador.textContent = `Búsqueda rápida en la pestaña activa (${filas.length} registros)`;
        }
    }
}

// ---------- GESTIÓN DE MODALES REQUERIDOS Y ESCAPE ----------
document.addEventListener("DOMContentLoaded", function () {
    const tbody = document.getElementById("filasModalRequeridos");
    const btnAgregar = document.getElementById("btnAgregarFilaRequerido");

    if (btnAgregar && tbody) {
        btnAgregar.addEventListener("click", function () {
            const primeraFila = tbody.querySelector(".fila-modal-requerido");
            if (primeraFila) {
                const nuevaFila = primeraFila.cloneNode(true);
                const sel = nuevaFila.querySelector('select[name="material_id[]"]');
                if (sel) sel.selectedIndex = 0;
                const inp = nuevaFila.querySelector('input[name="cantidad[]"]');
                if (inp) inp.value = "";
                tbody.appendChild(nuevaFila);
            }
        });

        tbody.addEventListener("click", function (e) {
            if (e.target.classList.contains("btnEliminarFilaReq")) {
                const filas = tbody.querySelectorAll(".fila-modal-requerido");
                if (filas.length > 1) {
                    e.target.closest(".fila-modal-requerido").remove();
                } else {
                    const fila = e.target.closest(".fila-modal-requerido");
                    const sel = fila.querySelector('select[name="material_id[]"]');
                    if (sel) sel.selectedIndex = 0;
                    const inp = fila.querySelector('input[name="cantidad[]"]');
                    if (inp) inp.value = "";
                }
            }
        });
    }

    // Buscador en vivo dentro del popover Excel
    const searchInput = document.getElementById("popoverSearchInput");
    if (searchInput) {
        searchInput.addEventListener("input", function () {
            const q = searchInput.value.toLowerCase().trim();
            const optionItems = document.querySelectorAll("#popoverCheckboxList .chk-option-item");
            
            optionItems.forEach(item => {
                const text = item.getAttribute("data-val-normalized") || "";
                if (text.includes(q)) {
                    item.classList.remove("hidden");
                } else {
                    item.classList.add("hidden");
                }
            });
        });
    }

    const buscadorMat = document.getElementById("buscadorMaterialesProyecto");
    const btnLimpiarMat = document.getElementById("btnLimpiarBuscadorMat");
    if (buscadorMat) {
        buscadorMat.addEventListener("input", filtrarMaterialesActivos);
        buscadorMat.addEventListener("keydown", function(e) {
            if (e.key === "Escape") {
                buscadorMat.value = "";
                filtrarMaterialesActivos();
            }
        });
    }
    if (btnLimpiarMat) {
        btnLimpiarMat.addEventListener("click", function() {
            if (buscadorMat) {
                buscadorMat.value = "";
                filtrarMaterialesActivos();
                buscadorMat.focus();
            }
        });
    }
    filtrarMaterialesActivos();
});

document.addEventListener("keydown", function (e) {
    if (e.key === "Escape") {
        cerrarFiltroExcel();
        const mReq = document.getElementById("modalPedirRequerido");
        if (mReq && !mReq.classList.contains("hidden")) {
            mReq.classList.add("hidden");
            mReq.classList.remove("flex");
        }
        const mDev = document.getElementById("modalRegistrarDevolucion");
        if (mDev && !mDev.classList.contains("hidden")) {
            mDev.classList.add("hidden");
            mDev.classList.remove("flex");
        }
    }
});

// =========================================================================
// MOTOR UNIVERSAL DE FILTROS TIPO EXCEL MULTI-TABLA
// =========================================================================
let colActualFiltro = null;
let tablaActualFiltro = null;
let nombreColActualFiltro = "";
let activeFiltersByTable = {
    'tablaDetalleBalance': {},
    'tablaDetalleDevoluciones': {},
    'tablaDetalleRequeridos': {},
    'tablaDetalleInstalados': {},
    'tablaDetalleRetiros': {}
};

function getActiveFilters(tablaId) {
    if (!activeFiltersByTable[tablaId]) {
        activeFiltersByTable[tablaId] = {};
    }
    return activeFiltersByTable[tablaId];
}

// Abrir Popover de Filtro Excel
function abrirFiltroExcel(event, colIdx, colName, tablaId = null) {
    event.stopPropagation();
    const btn = event.currentTarget;
    const th = btn.closest("th");
    const tabla = tablaId ? document.getElementById(tablaId) : btn.closest("table");
    if (!tabla) return;

    const idTabla = tabla.id;
    tablaActualFiltro = idTabla;

    if (colIdx === undefined || colIdx === null) {
        colIdx = th ? (th.hasAttribute("data-col-idx") ? parseInt(th.getAttribute("data-col-idx"), 10) : th.cellIndex) : 0;
    }
    colActualFiltro = colIdx;
    nombreColActualFiltro = colName || (th ? th.querySelector("span")?.innerText?.trim() : "Columna");

    const activeFilters = getActiveFilters(idTabla);

    // Obtener todas las filas de datos de esta tabla
    const tbody = tabla.querySelector("tbody");
    if (!tbody) return;
    const filas = Array.from(tbody.querySelectorAll("tr:not(.fila-vacia):not(.fila-no-filtro)"));

    // Contar valores distintos
    const counts = {};
    filas.forEach(f => {
        let val = "";
        if (f.hasAttribute(`data-col-${colIdx}`)) {
            val = (f.getAttribute(`data-col-${colIdx}`) || "").trim();
        } else if (f.children[colIdx]) {
            val = f.children[colIdx].innerText.replace(/\s+/g, " ").trim();
        }
        if (val === "") val = "(Vacío)";
        counts[val] = (counts[val] || 0) + 1;
    });

    const items = Object.keys(counts).map(v => ({ val: v, count: counts[v] }));
    items.sort((a, b) => a.val.localeCompare(b.val, undefined, { numeric: true, sensitivity: 'base' }));

    const popover = document.getElementById("excelFilterPopover");
    if (!popover) return;

    const popoverTitle = document.getElementById("popoverColName");
    const searchInput = document.getElementById("popoverSearchInput");
    const chkListContainer = document.getElementById("popoverCheckboxList");
    const chkSelectAll = document.getElementById("chkSelectAll");
    const btnClearThisCol = document.getElementById("btnClearThisCol");

    if (popoverTitle) popoverTitle.textContent = `Filtrar: ${nombreColActualFiltro}`;
    if (searchInput) searchInput.value = "";

    // Estado del botón borrar
    if (btnClearThisCol) {
        btnClearThisCol.style.display = activeFilters[colIdx] ? "flex" : "none";
    }

    const currentSelectedSet = activeFilters[colIdx] || null;

    if (chkListContainer) {
        chkListContainer.innerHTML = "";
        let todosMarcados = true;

        if (items.length === 0) {
            chkListContainer.innerHTML = '<div class="py-3 text-center text-muted-foreground text-xs italic">No hay registros disponibles en esta columna</div>';
            if (chkSelectAll) chkSelectAll.checked = false;
        } else {
            items.forEach((item) => {
                const isChecked = currentSelectedSet === null || currentSelectedSet.has(item.val);
                if (!isChecked) todosMarcados = false;

                const rowDiv = document.createElement("label");
                rowDiv.className = "flex items-center justify-between gap-2 px-1.5 py-1 rounded hover:bg-muted text-xs cursor-pointer chk-option-item";
                rowDiv.setAttribute("data-val-normalized", item.val.toLowerCase());

                rowDiv.innerHTML = `
                    <div class="flex items-center gap-2 truncate">
                        <input type="checkbox" value="${encodeURIComponent(item.val)}" class="chk-item-filter size-3.5 rounded text-primary focus:ring-0 cursor-pointer" ${isChecked ? "checked" : ""}>
                        <span class="truncate font-medium text-foreground">${item.val}</span>
                    </div>
                    <span class="text-[10px] px-1.5 py-0.2 bg-muted text-muted-foreground font-mono rounded-full shrink-0">${item.count}</span>
                `;
                chkListContainer.appendChild(rowDiv);
            });

            if (chkSelectAll) chkSelectAll.checked = todosMarcados;
        }
    }

    // Posicionar popover debajo del botón
    const rect = btn.getBoundingClientRect();
    const popoverWidth = 288;

    let leftPos = rect.left;
    if (leftPos + popoverWidth > window.innerWidth - 10) {
        leftPos = window.innerWidth - popoverWidth - 15;
    }
    if (leftPos < 10) leftPos = 10;

    let topPos = rect.bottom + 6;
    if (topPos + 360 > window.innerHeight) {
        topPos = Math.max(10, rect.top - 370);
    }

    popover.style.left = `${leftPos}px`;
    popover.style.top = `${topPos}px`;
    popover.classList.remove("hidden");

    setTimeout(() => {
        if (searchInput) searchInput.focus();
    }, 50);
}

// Cerrar Popover
function cerrarFiltroExcel() {
    const popover = document.getElementById("excelFilterPopover");
    if (popover) {
        popover.classList.add("hidden");
    }
    colActualFiltro = null;
}
function cerrarPopupFiltroExcel() {
    cerrarFiltroExcel();
}

// Seleccionar todo / Deseleccionar todo
function toggleSelectAllExcel(checked) {
    const visibleChkItems = document.querySelectorAll("#popoverCheckboxList .chk-option-item:not(.hidden) .chk-item-filter");
    visibleChkItems.forEach(chk => {
        chk.checked = checked;
    });
}

// Aplicar Filtro de Columna Actual
function aplicarFiltroColumnaActual() {
    if (colActualFiltro === null || !tablaActualFiltro) return;

    const activeFilters = getActiveFilters(tablaActualFiltro);
    const allChk = document.querySelectorAll("#popoverCheckboxList .chk-item-filter");
    const allTotal = allChk.length;
    let checkedCount = 0;
    const selectedSet = new Set();

    allChk.forEach(chk => {
        if (chk.checked) {
            checkedCount++;
            selectedSet.add(decodeURIComponent(chk.value));
        }
    });

    if (checkedCount === allTotal) {
        delete activeFilters[colActualFiltro];
    } else {
        activeFilters[colActualFiltro] = selectedSet;
    }

    cerrarFiltroExcel();
    ejecutarFiltradoTabla(tablaActualFiltro);
}

// Borrar Filtro de Columna Actual
function borrarFiltroColumnaActual() {
    if (colActualFiltro !== null && tablaActualFiltro) {
        const activeFilters = getActiveFilters(tablaActualFiltro);
        delete activeFilters[colActualFiltro];
        cerrarFiltroExcel();
        ejecutarFiltradoTabla(tablaActualFiltro);
    }
}

// Limpiar todos los filtros de una tabla o de todas
function limpiarTodosLosFiltrosExcel(tablaId = null) {
    if (tablaId && activeFiltersByTable[tablaId]) {
        activeFiltersByTable[tablaId] = {};
        ejecutarFiltradoTabla(tablaId);
    } else if (tablaId) {
        activeFiltersByTable[tablaId] = {};
        ejecutarFiltradoTabla(tablaId);
    } else {
        for (const t in activeFiltersByTable) {
            activeFiltersByTable[t] = {};
            ejecutarFiltradoTabla(t);
        }
    }
}
window.limpiarTodosLosFiltrosExcel = limpiarTodosLosFiltrosExcel;
window.limpiarTodosFiltrosTabla = limpiarTodosLosFiltrosExcel;

// Ordenar filas A-Z / Z-A
function ejecutarSortExcel(ascendente) {
    if (colActualFiltro === null || !tablaActualFiltro) return;
    const colIdx = colActualFiltro;
    const tabla = document.getElementById(tablaActualFiltro);
    if (!tabla) return;
    const tbody = tabla.querySelector("tbody");
    if (!tbody) return;
    const filas = Array.from(tbody.querySelectorAll("tr:not(.fila-vacia):not(.fila-no-filtro)"));

    filas.sort((a, b) => {
        let valA = a.hasAttribute(`data-col-${colIdx}`) ? a.getAttribute(`data-col-${colIdx}`) : (a.children[colIdx] ? a.children[colIdx].innerText : "");
        let valB = b.hasAttribute(`data-col-${colIdx}`) ? b.getAttribute(`data-col-${colIdx}`) : (b.children[colIdx] ? b.children[colIdx].innerText : "");
        valA = (valA || "").trim();
        valB = (valB || "").trim();

        const dateA = parseFecha(valA);
        const dateB = parseFecha(valB);
        if (dateA && dateB) {
            return ascendente ? dateA - dateB : dateB - dateA;
        }

        const numA = parseFloat(valA.replace(/[^0-9.-]+/g, ""));
        const numB = parseFloat(valB.replace(/[^0-9.-]+/g, ""));
        if (!isNaN(numA) && !isNaN(numB) && !valA.includes("/") && !valB.includes("/")) {
            return ascendente ? numA - numB : numB - numA;
        }

        return ascendente ? valA.localeCompare(valB, undefined, { numeric: true }) : valB.localeCompare(valA, undefined, { numeric: true });
    });

    filas.forEach(f => tbody.appendChild(f));
    cerrarFiltroExcel();
}

function parseFecha(str) {
    if (!str || !str.includes("/")) return null;
    const parts = str.split("/");
    if (parts.length === 3) {
        const d = parseInt(parts[0], 10);
        const m = parseInt(parts[1], 10) - 1;
        const y = parseInt(parts[2], 10);
        return new Date(y, m, d);
    }
    return null;
}

// Motor de filtrado por tabla
function ejecutarFiltradoTabla(tablaId) {
    const tabla = document.getElementById(tablaId);
    if (!tabla) return;
    const tbody = tabla.querySelector("tbody");
    if (!tbody) return;

    const activeFilters = getActiveFilters(tablaId);
    const activeCols = Object.keys(activeFilters).map(k => parseInt(k, 10));
    const filas = Array.from(tbody.querySelectorAll("tr:not(.fila-vacia):not(.fila-no-filtro)"));
    let visiblesCount = 0;

    filas.forEach(f => {
        let cumple = true;

        if (activeCols.length > 0) {
            for (const col of activeCols) {
                const setValores = activeFilters[col];
                let val = "";
                if (f.hasAttribute(`data-col-${col}`)) {
                    val = (f.getAttribute(`data-col-${col}`) || "").trim();
                } else if (f.children[col]) {
                    val = f.children[col].innerText.replace(/\s+/g, " ").trim();
                }
                if (val === "") val = "(Vacío)";
                if (!setValores.has(val)) {
                    cumple = false;
                    break;
                }
            }
        }

        if (cumple) {
            f.dataset.ocultoPorExcel = "false";
            visiblesCount++;
        } else {
            f.dataset.ocultoPorExcel = "true";
        }
    });

    filtrarMaterialesActivos();

    // Actualizar botones de encabezado para esta tabla
    const ths = tabla.querySelectorAll("th.th-excel-col");
    ths.forEach(th => {
        const cIdx = th.hasAttribute("data-col-idx") ? parseInt(th.getAttribute("data-col-idx"), 10) : th.cellIndex;
        const btn = th.querySelector(".btn-filter-trigger");
        if (btn) {
            if (activeFilters[cIdx]) {
                th.classList.add("has-active-filter");
                btn.classList.add("filter-active");
                btn.innerHTML = '<span class="text-amber-950 font-black text-[10px]">▼✓</span>';
            } else {
                th.classList.remove("has-active-filter");
                btn.classList.remove("filter-active");
                btn.innerHTML = '<span class="icon-arrow text-[10px]">▼</span>';
            }
        }
    });

    // Actualizar barra de estado de filtros si existe
    const barraMap = {
        'tablaDetalleInstalados': { barra: 'barraFiltrosInstalados', texto: 'textoFiltrosInstalados' },
        'tablaDetalleRetiros': { barra: 'barraFiltrosRetiros', texto: 'textoFiltrosRetiros' }
    };

    if (barraMap[tablaId]) {
        const barra = document.getElementById(barraMap[tablaId].barra);
        const texto = document.getElementById(barraMap[tablaId].texto);
        if (barra && texto) {
            if (activeCols.length > 0) {
                barra.classList.remove('hidden');
                barra.classList.add('flex');
                texto.textContent = `${visiblesCount} de ${filas.length} registros visibles (${activeCols.length} columna(s) filtrada(s))`;
            } else {
                barra.classList.add('hidden');
                barra.classList.remove('flex');
            }
        }
    }
}

// Clic fuera del popover para cerrarlo
document.addEventListener("click", function (e) {
    const popover = document.getElementById("excelFilterPopover");
    if (popover && !popover.classList.contains("hidden")) {
        if (!popover.contains(e.target) && !e.target.closest(".btn-filter-trigger")) {
            cerrarFiltroExcel();
        }
    }
});
