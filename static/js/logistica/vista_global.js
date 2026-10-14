/**
 * COINTECA S.A.S. - Módulo de Logística
 * vista_global.js - Motor de filtrado tipo Excel multi-tabla, búsqueda general en vivo y ordenamiento dinámico.
 */

// ---------- ESTADO GLOBAL DE FILTROS TIPO EXCEL POR TABLA ----------
let colActualFiltro = null;
let tablaActualFiltro = "tablaNodosGlobal";
let nombreColActualFiltro = "";
let activeFiltersByTable = {
    'tablaNodosGlobal': {},
    'tablaDevolucionesGlobal': {},
    'tablaBalanceGlobal': {},
    'tablaRetirosGlobal': {},
    'tablaResumenEntradasGlobal': {}
};

function getActiveFilters(tablaId) {
    if (!activeFiltersByTable[tablaId]) {
        activeFiltersByTable[tablaId] = {};
    }
    return activeFiltersByTable[tablaId];
}

// ---------- PESTAÑAS PRINCIPALES ----------
function cambiarPestanaGlobal(tabName) {
    const paneles = {
        'nodos': document.getElementById('panelNodos'),
        'devoluciones': document.getElementById('panelDevoluciones'),
        'balance': document.getElementById('panelBalance'),
        'retiros': document.getElementById('panelRetiros'),
        'entradas': document.getElementById('panelEntradas')
    };

    const botones = {
        'nodos': document.getElementById('tabBtnNodos'),
        'devoluciones': document.getElementById('tabBtnDevoluciones'),
        'balance': document.getElementById('tabBtnBalance'),
        'retiros': document.getElementById('tabBtnRetiros'),
        'entradas': document.getElementById('tabBtnEntradas')
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

    for (const key in botones) {
        if (botones[key]) {
            if (key === tabName) {
                botones[key].className = 'py-3 px-5 text-sm transition flex items-center gap-2 whitespace-nowrap border-b-2 border-indigo-600 text-indigo-700 font-bold tab-btn-global';
            } else {
                botones[key].className = 'py-3 px-5 text-sm transition flex items-center gap-2 whitespace-nowrap text-muted-foreground hover:text-gray-700 tab-btn-global';
            }
        }
    }
}

// ---------- ABRIR POPUP DE FILTRO EXCEL (UNIVERSAL MULTI-TABLA) ----------
function abrirFiltroExcel(event, colIdx, colName, tablaId = null) {
    event.stopPropagation();
    const btn = event.currentTarget;
    const th = btn.closest("th");
    const tabla = tablaId? document.getElementById(tablaId): (btn.closest("table") || document.getElementById("tablaNodosGlobal"));
    if (!tabla) return;

    const idTabla = tabla.id || "tablaNodosGlobal";
    tablaActualFiltro = idTabla;

    if (colIdx === undefined || colIdx === null) {
        colIdx = th? (th.hasAttribute("data-col-idx")? parseInt(th.getAttribute("data-col-idx"), 10): th.cellIndex): 0;
    }
    colActualFiltro = colIdx;
    nombreColActualFiltro = colName || (th? th.querySelector("span")?.innerText?.trim(): "Columna");

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
        btnClearThisCol.style.display = activeFilters[colIdx]? "flex": "none";
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
                        <input type="checkbox" value="${encodeURIComponent(item.val)}" class="chk-item-filter size-3.5 rounded text-primary focus:ring-0 cursor-pointer" ${isChecked? "checked": ""}>
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

// ---------- CERRAR POPUP DE FILTRO EXCEL ----------
function cerrarFiltroExcel() {
    const popover = document.getElementById("excelFilterPopover");
    if (popover) {
        popover.classList.add("hidden");
    }
    colActualFiltro = null;
}

// ---------- TOGGLE SELECCIONAR TODO ----------
function toggleSelectAllExcel(checked) {
    const visibleChkItems = document.querySelectorAll("#popoverCheckboxList.chk-option-item:not(.hidden).chk-item-filter");
    visibleChkItems.forEach(chk => {
        chk.checked = checked;
    });
}

// ---------- BUSCADOR EN VIVO DENTRO DEL POPUP ----------
document.addEventListener("DOMContentLoaded", function () {
    const searchInput = document.getElementById("popoverSearchInput");
    if (searchInput) {
        searchInput.addEventListener("input", function () {
            const q = searchInput.value.toLowerCase().trim();
            const optionItems = document.querySelectorAll("#popoverCheckboxList.chk-option-item");
            
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
});

// ---------- APLICAR FILTRO DE LA COLUMNA ACTUAL ----------
function aplicarFiltroColumnaActual() {
    if (colActualFiltro === null ||!tablaActualFiltro) return;

    const activeFilters = getActiveFilters(tablaActualFiltro);
    const allChk = document.querySelectorAll("#popoverCheckboxList.chk-item-filter");
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

// ---------- BORRAR FILTRO DE COLUMNA ACTUAL ----------
function borrarFiltroColumnaActual() {
    if (colActualFiltro!== null && tablaActualFiltro) {
        const activeFilters = getActiveFilters(tablaActualFiltro);
        delete activeFilters[colActualFiltro];
        cerrarFiltroExcel();
        ejecutarFiltradoTabla(tablaActualFiltro);
    }
}

// ---------- LIMPIAR TODOS LOS FILTROS DE UNA TABLA ----------
function limpiarTodosFiltrosTabla(tablaId = "tablaNodosGlobal") {
    activeFiltersByTable[tablaId] = {};
    if (tablaId === "tablaNodosGlobal") {
        const inputGlobal = document.getElementById("inputBuscadorGlobal");
        if (inputGlobal) inputGlobal.value = "";
    }
    ejecutarFiltradoTabla(tablaId);
}

function limpiarTodosFiltrosExcel() {
    limpiarTodosFiltrosTabla("tablaNodosGlobal");
}

// ---------- ORDENAR FILAS A-Z / Z-A ----------
function ejecutarSortExcel(ascendente) {
    if (colActualFiltro === null ||!tablaActualFiltro) return;
    const colIdx = colActualFiltro;
    const tabla = document.getElementById(tablaActualFiltro);
    if (!tabla) return;
    const tbody = tabla.querySelector("tbody");
    if (!tbody) return;
    const filas = Array.from(tbody.querySelectorAll("tr:not(.fila-vacia):not(.fila-no-filtro)"));

    filas.sort((a, b) => {
        let valA = a.hasAttribute(`data-col-${colIdx}`)? a.getAttribute(`data-col-${colIdx}`): (a.children[colIdx]? a.children[colIdx].innerText: "");
        let valB = b.hasAttribute(`data-col-${colIdx}`)? b.getAttribute(`data-col-${colIdx}`): (b.children[colIdx]? b.children[colIdx].innerText: "");
        valA = (valA || "").trim();
        valB = (valB || "").trim();

        const dateA = parseFecha(valA);
        const dateB = parseFecha(valB);
        if (dateA && dateB) {
            return ascendente? dateA - dateB: dateB - dateA;
        }

        const numA = parseFloat(valA.replace(/[^0-9.-]+/g, ""));
        const numB = parseFloat(valB.replace(/[^0-9.-]+/g, ""));
        if (!isNaN(numA) &&!isNaN(numB) &&!valA.includes("/") &&!valB.includes("/")) {
            return ascendente? numA - numB: numB - numA;
        }

        return ascendente? valA.localeCompare(valB, undefined, { numeric: true }): valB.localeCompare(valA, undefined, { numeric: true });
    });

    filas.forEach(f => tbody.appendChild(f));
    cerrarFiltroExcel();
}

function parseFecha(str) {
    if (!str ||!str.includes("/")) return null;
    const parts = str.split("/");
    if (parts.length === 3) {
        const d = parseInt(parts[0], 10);
        const m = parseInt(parts[1], 10) - 1;
        const y = parseInt(parts[2], 10);
        return new Date(y, m, d);
    }
    return null;
}

// ---------- MOTOR DE FILTRADO Y RECÁLCULO MULTI-TABLA ----------
function ejecutarFiltradoTabla(tablaId) {
    const tabla = document.getElementById(tablaId);
    if (!tabla) return;
    const tbody = tabla.querySelector("tbody");
    if (!tbody) return;

    const activeFilters = getActiveFilters(tablaId);
    const activeCols = Object.keys(activeFilters).map(k => parseInt(k, 10));

    let qGlobal = "";
    if (tablaId === "tablaNodosGlobal") {
        const inputGlobal = document.getElementById("inputBuscadorGlobal");
        qGlobal = inputGlobal? inputGlobal.value.toLowerCase().trim(): "";
    }

    const filas = Array.from(tbody.querySelectorAll("tr:not(.fila-vacia):not(.fila-no-filtro)"));
    let visiblesCount = 0;
    const colMatTotals = {};

    filas.forEach(f => {
        let cumple = true;

        if (qGlobal!== "") {
            const txt = f.textContent.toLowerCase();
            if (!txt.includes(qGlobal)) cumple = false;
        }

        if (cumple && activeCols.length > 0) {
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
            f.style.display = "";
            visiblesCount++;

            const celdasMat = f.querySelectorAll(".celda-material");
            celdasMat.forEach(c => {
                const mIdx = c.getAttribute("data-mat-idx");
                if (!colMatTotals[mIdx]) colMatTotals[mIdx] = { inst: 0, ret: 0 };
                colMatTotals[mIdx].inst += parseFloat(c.getAttribute("data-cant-inst")) || 0;
                colMatTotals[mIdx].ret += parseFloat(c.getAttribute("data-cant-ret")) || 0;
            });
        } else {
            f.style.display = "none";
        }
    });

    // Actualizar botones de encabezado para esta tabla
    const ths = tabla.querySelectorAll("th.th-excel-col");
    ths.forEach(th => {
        const cIdx = th.hasAttribute("data-col-idx")? parseInt(th.getAttribute("data-col-idx"), 10): th.cellIndex;
        const btn = th.querySelector(".btn-filter-trigger");
        if (btn) {
            if (activeFilters[cIdx]) {
                th.classList.add("has-active-filter");
                btn.classList.add("filter-active");
                btn.innerHTML = '<span class="text-amber-950 font-black text-[10px]">▼</span>';
            } else {
                th.classList.remove("has-active-filter");
                btn.classList.remove("filter-active");
                btn.innerHTML = '<span class="icon-arrow text-[10px]">▼</span>';
            }
        }
    });

    // Si es tablaNodosGlobal, actualizar contadores específicos y tfoot
    if (tablaId === "tablaNodosGlobal") {
        const countSpan = document.getElementById("nodosVisiblesCount");
        if (countSpan) countSpan.textContent = visiblesCount;

        const tfootNodeSpan = document.getElementById("tfootContadorNodos");
        if (tfootNodeSpan) tfootNodeSpan.textContent = visiblesCount;

        const btnLimpiar = document.getElementById("btnLimpiarTodosFiltros");
        const spanNumFiltros = document.getElementById("filtrosActivosNum");
        if (btnLimpiar && spanNumFiltros) {
            const numActivos = activeCols.length + (qGlobal? 1: 0);
            spanNumFiltros.textContent = numActivos;
            if (numActivos > 0) {
                btnLimpiar.classList.remove("hidden");
            } else {
                btnLimpiar.classList.add("hidden");
            }
        }

        const tfootCeldas = document.querySelectorAll(".tfoot-col-mat");
        tfootCeldas.forEach(tc => {
            const mIdx = tc.getAttribute("data-mat-idx");
            const tot = colMatTotals[mIdx] || { inst: 0, ret: 0 };
            const valInstDiv = tc.querySelector(".tfoot-val-inst");
            const valRetDiv = tc.querySelector(".tfoot-val-ret");

            if (valInstDiv) {
                valInstDiv.textContent = Number.isInteger(tot.inst)? tot.inst: tot.inst.toFixed(1);
            }
            if (valRetDiv) {
                if (tot.ret > 0) {
                    valRetDiv.classList.remove("hidden");
                    valRetDiv.textContent = `Ret: ${Number.isInteger(tot.ret)? tot.ret: tot.ret.toFixed(1)}`;
                } else {
                    valRetDiv.classList.add("hidden");
                }
            }
        });
    }
}

function ejecutarFiltradoGeneral() {
    ejecutarFiltradoTabla("tablaNodosGlobal");
}

// ---------- EVENTOS DE CLIC FUERA Y TECLADO ----------
document.addEventListener("click", function (e) {
    const popover = document.getElementById("excelFilterPopover");
    if (popover &&!popover.classList.contains("hidden")) {
        if (!popover.contains(e.target) &&!e.target.closest(".btn-filter-trigger")) {
            cerrarFiltroExcel();
        }
    }
});

document.addEventListener("keydown", function (e) {
    if (e.key === "Escape") {
        cerrarFiltroExcel();
    }
});

// ---------- SINCRONIZACIÓN DE SELECTORES DINÁMICOS ----------
document.addEventListener("DOMContentLoaded", function () {
    const selectMacro = document.getElementById("selectMacroproyecto");
    const selectProy = document.getElementById("selectProyecto");
    const inputBuscador = document.getElementById("inputBuscadorGlobal");
    const todosProyectosData = JSON.parse(document.getElementById("proyectos-global-json")?.textContent || "[]");

    // Selector dependiente con envío automático
    if (selectMacro && selectProy) {
        selectMacro.addEventListener("change", function () {
            const macroId = selectMacro.value;

            selectProy.innerHTML = macroId?
                `<option value="todos"> Todos los Proyectos de este Macroproyecto (Consolidado)</option>`:
                `<option value="todos"> Todos los Macroproyectos y Proyectos (Global)</option>`;

            const filtrados = macroId? todosProyectosData.filter(p => String(p.macro_id) === String(macroId)): todosProyectosData;

            filtrados.forEach(p => {
                const opt = document.createElement("option");
                opt.value = p.id;
                opt.textContent = `Proyecto ${p.numero} (${p.macro_nombre}) - ${p.tipo}`;
                selectProy.appendChild(opt);
            });

            const form = document.getElementById("formFiltroGlobal");
            if (form) form.submit();
        });

        selectProy.addEventListener("change", function () {
            const form = document.getElementById("formFiltroGlobal");
            if (form) form.submit();
        });
    }

    // Buscador general en vivo
    if (inputBuscador) {
        inputBuscador.addEventListener("input", function () {
            ejecutarFiltradoGeneral();

            // Filtrar también en pestaña de balance
            const q = inputBuscador.value.toLowerCase().trim();
            const filasBalance = document.querySelectorAll(".fila-balance-global");
            filasBalance.forEach(f => {
                const txt = f.textContent.toLowerCase();
                f.style.display = txt.includes(q)? "": "none";
            });
        });
    }
});
