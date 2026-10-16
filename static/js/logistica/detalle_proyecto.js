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

        if (coincideBuscador &&!ocultoPorExcel) {
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
// =========================================================================
// MODAL: PEDIR / AGREGAR MATERIALES REQUERIDOS (AUTOCOMPLETE + LISTA DIRECTA)
// =========================================================================
let catalogoMateriales = [];
let itemsParaRequerir = [];
let indiceSugerenciaActiva = -1;

function abrirModalPedirRequerido() {
    cargarCatalogoMateriales();
    const m = document.getElementById("modalPedirRequerido");
    if (m) {
        m.classList.remove("hidden");
        m.classList.add("flex");
        setTimeout(function () {
            const inp = document.getElementById("inputBuscadorMaterialModal");
            if (inp) inp.focus();
        }, 100);
    }
}

function cerrarModalPedirRequerido() {
    const m = document.getElementById("modalPedirRequerido");
    if (m) {
        m.classList.add("hidden");
        m.classList.remove("flex");
        cerrarDropdownSugerencias();
    }
}

function cerrarDropdownSugerencias() {
    const dropdown = document.getElementById("dropdownSugerenciasMaterial");
    if (dropdown) {
        dropdown.classList.add("hidden");
        dropdown.innerHTML = "";
    }
    indiceSugerenciaActiva = -1;
}

function normalizarTexto(txt) {
    if (!txt) return "";
    return txt.toString().toLowerCase().normalize("NFD").replace(/[\u0300-\u036f]/g, "").trim();
}

function cargarCatalogoMateriales() {
    const script = document.getElementById("catalogoMaterialesData");
    if (script && catalogoMateriales.length === 0) {
        try {
            catalogoMateriales = JSON.parse(script.textContent || "[]");
        } catch (e) {
            console.error("Error parseando catálogo de materiales:", e);
        }
    }
}

function seleccionarMaterialModal(mat) {
    const inputBuscador = document.getElementById("inputBuscadorMaterialModal");
    const btnLimpiar = document.getElementById("btnLimpiarMaterialModal");
    const hiddenId = document.getElementById("modalSelMaterialId");
    const hiddenItem = document.getElementById("modalSelMaterialItem");
    const hiddenDesc = document.getElementById("modalSelMaterialDesc");
    const hiddenUnidad = document.getElementById("modalSelMaterialUnidad");
    const badgeUnidad = document.getElementById("badgeUnidadModal");
    const textoUnidad = document.getElementById("textoUnidadModal");
    const inputCantidad = document.getElementById("inputCantidadMaterialModal");

    if (hiddenId) hiddenId.value = mat.id;
    if (hiddenItem) hiddenItem.value = mat.item || "";
    if (hiddenDesc) hiddenDesc.value = mat.descripcion || "";
    if (hiddenUnidad) hiddenUnidad.value = mat.unidad || "UN";

    if (inputBuscador) {
        inputBuscador.value = (mat.item ? `[${mat.item}] ` : "") + mat.descripcion;
    }
    if (btnLimpiar) btnLimpiar.classList.remove("hidden");

    if (textoUnidad) textoUnidad.textContent = mat.unidad || "UN";
    if (badgeUnidad) {
        badgeUnidad.className = "h-[38px] flex items-center justify-center px-2 py-1.5 rounded-lg border-2 border-blue-400 bg-blue-100 text-blue-900 font-black text-xs text-center transition";
    }

    cerrarDropdownSugerencias();

    if (inputCantidad) {
        inputCantidad.focus();
        inputCantidad.select();
    }
}

function limpiarSeleccionMaterialModal() {
    const inputBuscador = document.getElementById("inputBuscadorMaterialModal");
    const btnLimpiar = document.getElementById("btnLimpiarMaterialModal");
    const hiddenId = document.getElementById("modalSelMaterialId");
    const hiddenItem = document.getElementById("modalSelMaterialItem");
    const hiddenDesc = document.getElementById("modalSelMaterialDesc");
    const hiddenUnidad = document.getElementById("modalSelMaterialUnidad");
    const badgeUnidad = document.getElementById("badgeUnidadModal");
    const textoUnidad = document.getElementById("textoUnidadModal");
    const inputCantidad = document.getElementById("inputCantidadMaterialModal");

    if (inputBuscador) inputBuscador.value = "";
    if (btnLimpiar) btnLimpiar.classList.add("hidden");
    if (hiddenId) hiddenId.value = "";
    if (hiddenItem) hiddenItem.value = "";
    if (hiddenDesc) hiddenDesc.value = "";
    if (hiddenUnidad) hiddenUnidad.value = "";
    if (textoUnidad) textoUnidad.textContent = "—";
    if (badgeUnidad) {
        badgeUnidad.className = "h-[38px] flex items-center justify-center px-2 py-1.5 rounded-lg border-2 border-slate-300 bg-slate-100 text-slate-500 font-black text-xs text-center transition";
    }
    if (inputCantidad) inputCantidad.value = "";
    cerrarDropdownSugerencias();
    if (inputBuscador) inputBuscador.focus();
}

function agregarMaterialALaLista() {
    const hiddenId = document.getElementById("modalSelMaterialId");
    const hiddenItem = document.getElementById("modalSelMaterialItem");
    const hiddenDesc = document.getElementById("modalSelMaterialDesc");
    const hiddenUnidad = document.getElementById("modalSelMaterialUnidad");
    const inputCantidad = document.getElementById("inputCantidadMaterialModal");
    const inputBuscador = document.getElementById("inputBuscadorMaterialModal");

    const matId = hiddenId ? hiddenId.value : "";
    if (!matId) {
        alert("Por favor selecciona un material del catálogo.");
        if (inputBuscador) inputBuscador.focus();
        return;
    }

    const cantRaw = inputCantidad ? inputCantidad.value.trim().replace(",", ".") : "";
    const cantNum = parseFloat(cantRaw);
    if (isNaN(cantNum) || cantNum <= 0) {
        alert("Por favor ingresa una cantidad válida mayor a 0.");
        if (inputCantidad) inputCantidad.focus();
        return;
    }

    const itemCode = hiddenItem ? hiddenItem.value : "";
    const desc = hiddenDesc ? hiddenDesc.value : "";
    const unidad = hiddenUnidad ? hiddenUnidad.value : "UN";

    const existente = itemsParaRequerir.find(function (it) {
        return String(it.material_id) === String(matId);
    });

    if (existente) {
        existente.cantidad += cantNum;
    } else {
        itemsParaRequerir.push({
            material_id: matId,
            item: itemCode,
            descripcion: desc,
            unidad: unidad,
            cantidad: cantNum
        });
    }

    renderizarTablaRequeridosModal();
    limpiarSeleccionMaterialModal();
}

function eliminarItemRequeridoModal(idx) {
    itemsParaRequerir.splice(idx, 1);
    renderizarTablaRequeridosModal();
}

function renderizarTablaRequeridosModal() {
    const tbody = document.getElementById("cuerpoTablaRequeridosModal");
    const contador = document.getElementById("contadorItemsListaModal");
    const btnGuardar = document.getElementById("btnGuardarRequeridosModal");
    if (!tbody) return;

    if (contador) {
        const n = itemsParaRequerir.length;
        contador.textContent = n + (n === 1 ? " material" : " materiales");
    }

    if (itemsParaRequerir.length === 0) {
        tbody.innerHTML = `
            <tr id="filaVaciaRequeridosModal">
                <td colspan="5" class="px-4 py-8 text-center text-slate-400 text-xs">
                    <div class="space-y-1">
                        <p class="font-bold text-slate-600 text-sm">Aún no has agregado materiales a la lista.</p>
                        <p class="text-slate-400">Busca el material arriba, digita la cantidad y haz clic en <strong>"+ Agregar"</strong>.</p>
                    </div>
                </td>
            </tr>
        `;
        if (btnGuardar) btnGuardar.disabled = true;
        return;
    }

    if (btnGuardar) btnGuardar.disabled = false;

    tbody.innerHTML = itemsParaRequerir.map(function (it, idx) {
        const cantFormatted = it.cantidad % 1 === 0 ? it.cantidad : it.cantidad.toFixed(2);
        return `
            <tr class="hover:bg-blue-50/50 transition">
                <td class="px-3 py-2.5 text-center font-mono text-xs font-bold text-slate-600">
                    ${it.item || "—"}
                    <input type="hidden" name="material_id[]" value="${it.material_id}">
                </td>
                <td class="px-4 py-2.5 font-semibold text-slate-900 text-xs">
                    ${it.descripcion}
                </td>
                <td class="px-3 py-2.5 text-center text-xs font-bold">
                    <span class="px-2 py-0.5 rounded bg-blue-100 text-blue-900 border border-blue-200">${it.unidad}</span>
                </td>
                <td class="px-4 py-2.5 text-right font-black text-blue-950 text-sm">
                    ${cantFormatted}
                    <input type="hidden" name="cantidad[]" value="${it.cantidad}">
                </td>
                <td class="px-3 py-2.5 text-center">
                    <button type="button" onclick="eliminarItemRequeridoModal(${idx})"
                            class="text-rose-600 hover:text-rose-800 hover:bg-rose-50 p-1 rounded transition text-base font-black cursor-pointer leading-none"
                            title="Quitar este material de la lista">
                        &times;
                    </button>
                </td>
            </tr>
        `;
    }).join("");
}

function buscarMaterialesPriorizados(query, catalogo) {
    const qNorm = normalizarTexto(query);
    if (!qNorm) return [];

    const palabras = qNorm.split(/\s+/).filter(p => p.length > 0);
    const resultadosScored = [];

    for (let i = 0; i < catalogo.length; i++) {
        const m = catalogo[i];
        const itemNorm = normalizarTexto(m.item);
        const descNorm = normalizarTexto(m.descripcion);
        const fullTexto = `${itemNorm} ${descNorm}`;

        // Debe contener todas las palabras de búsqueda
        const contieneTodas = palabras.every(p => fullTexto.includes(p));
        if (!contieneTodas) continue;

        // Calcular puntaje de relevancia (1 es máxima prioridad)
        let score = 4;
        const palabrasDesc = descNorm.split(/\s+/);

        if (descNorm.startsWith(qNorm)) {
            // Empieza exactamente por la letra o término (ej: "s" -> "seccionador...", "b" -> "bisagra...", "abraza" -> "abrazadera...")
            score = 1;
        } else if (palabrasDesc.some(w => w.startsWith(qNorm))) {
            // Alguna palabra interior empieza por el término (ej: "serv" -> "sum/inst serv...", "cobre" -> "cable cobre...")
            score = 2;
        } else if (itemNorm.startsWith(qNorm)) {
            // El código empieza por el término
            score = 3;
        } else {
            // Coincidencia dentro de la descripción o código
            score = 4;
        }

        resultadosScored.push({
            score: score,
            desc: descNorm,
            material: m
        });
    }

    // Ordenar primero por prioridad (score 1 antes que 2, 3, 4) y luego alfabéticamente
    resultadosScored.sort(function (a, b) {
        if (a.score !== b.score) {
            return a.score - b.score;
        }
        return a.desc.localeCompare(b.desc);
    });

    return resultadosScored.slice(0, 30).map(x => x.material);
}

document.addEventListener("DOMContentLoaded", function () {
    cargarCatalogoMateriales();

    const inputBuscador = document.getElementById("inputBuscadorMaterialModal");
    const dropdown = document.getElementById("dropdownSugerenciasMaterial");
    const btnLimpiar = document.getElementById("btnLimpiarMaterialModal");
    const inputCantidad = document.getElementById("inputCantidadMaterialModal");
    const btnAgregar = document.getElementById("btnAgregarAListaModal");
    const modalEl = document.getElementById("modalPedirRequerido");

    if (inputBuscador && dropdown) {
        inputBuscador.addEventListener("input", function () {
            const query = normalizarTexto(inputBuscador.value);
            if (btnLimpiar) {
                if (inputBuscador.value.trim().length > 0) {
                    btnLimpiar.classList.remove("hidden");
                } else {
                    btnLimpiar.classList.add("hidden");
                }
            }

            if (query.length < 1) {
                cerrarDropdownSugerencias();
                return;
            }

            cargarCatalogoMateriales();
            const resultados = buscarMaterialesPriorizados(query, catalogoMateriales);

            if (resultados.length === 0) {
                dropdown.innerHTML = `
                    <div class="px-4 py-3 text-xs text-slate-400 text-center">
                        No se encontraron materiales que coincidan con "<strong>${inputBuscador.value}</strong>"
                    </div>
                `;
                dropdown.classList.remove("hidden");
                return;
            }

            dropdown.innerHTML = resultados.map(function (m, idx) {
                return `
                    <div class="px-3.5 py-2.5 hover:bg-blue-50 cursor-pointer flex items-center justify-between gap-2 item-sugerencia-material transition"
                         data-idx="${idx}">
                        <div class="flex items-center gap-2 truncate">
                            <span class="font-mono font-bold text-xs px-1.5 py-0.5 rounded bg-slate-100 text-slate-700 shrink-0">${m.item || "S/C"}</span>
                            <span class="font-semibold text-xs text-slate-900 truncate">${m.descripcion}</span>
                        </div>
                        <span class="text-[11px] font-black px-2 py-0.5 rounded bg-blue-100 text-blue-900 shrink-0 border border-blue-200">
                            ${m.unidad || "UN"}
                        </span>
                    </div>
                `;
            }).join("");

            dropdown.querySelectorAll(".item-sugerencia-material").forEach(function (el, idx) {
                el.addEventListener("click", function () {
                    seleccionarMaterialModal(resultados[idx]);
                });
            });

            indiceSugerenciaActiva = -1;
            dropdown.classList.remove("hidden");
        });

        inputBuscador.addEventListener("keydown", function (e) {
            const items = dropdown.querySelectorAll(".item-sugerencia-material");
            if (!dropdown.classList.contains("hidden") && items.length > 0) {
                if (e.key === "ArrowDown") {
                    e.preventDefault();
                    indiceSugerenciaActiva = (indiceSugerenciaActiva + 1) % items.length;
                    actualizarResaltadoSugerencia(items);
                    return;
                }
                if (e.key === "ArrowUp") {
                    e.preventDefault();
                    indiceSugerenciaActiva = (indiceSugerenciaActiva - 1 + items.length) % items.length;
                    actualizarResaltadoSugerencia(items);
                    return;
                }
                if (e.key === "Enter") {
                    e.preventDefault();
                    if (indiceSugerenciaActiva >= 0 && indiceSugerenciaActiva < items.length) {
                        items[indiceSugerenciaActiva].click();
                    } else if (items.length > 0) {
                        items[0].click();
                    }
                    return;
                }
                if (e.key === "Escape") {
                    cerrarDropdownSugerencias();
                    return;
                }
            }
        });
    }

    function actualizarResaltadoSugerencia(items) {
        items.forEach((it, idx) => {
            if (idx === indiceSugerenciaActiva) {
                it.classList.add("bg-blue-100");
                it.scrollIntoView({ block: "nearest" });
            } else {
                it.classList.remove("bg-blue-100");
            }
        });
    }

    if (btnLimpiar) {
        btnLimpiar.addEventListener("click", limpiarSeleccionMaterialModal);
    }

    if (btnAgregar) {
        btnAgregar.addEventListener("click", agregarMaterialALaLista);
    }

    if (inputCantidad) {
        inputCantidad.addEventListener("keydown", function (e) {
            if (e.key === "Enter") {
                e.preventDefault();
                agregarMaterialALaLista();
            }
        });
    }

    if (modalEl) {
        modalEl.addEventListener("click", function (e) {
            if (e.target === modalEl) {
                cerrarModalPedirRequerido();
            }
        });
    }

    document.addEventListener("click", function (e) {
        if (dropdown && !dropdown.contains(e.target) && e.target !== inputBuscador) {
            cerrarDropdownSugerencias();
        }
    });

    // Buscador en vivo dentro del popover Excel
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
        if (mReq &&!mReq.classList.contains("hidden")) {
            mReq.classList.add("hidden");
            mReq.classList.remove("flex");
        }
        const mDev = document.getElementById("modalRegistrarDevolucion");
        if (mDev &&!mDev.classList.contains("hidden")) {
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
    const tabla = tablaId? document.getElementById(tablaId): btn.closest("table");
    if (!tabla) return;

    const idTabla = tabla.id;
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
    const visibleChkItems = document.querySelectorAll("#popoverCheckboxList.chk-option-item:not(.hidden).chk-item-filter");
    visibleChkItems.forEach(chk => {
        chk.checked = checked;
    });
}

// Aplicar Filtro de Columna Actual
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

// Borrar Filtro de Columna Actual
function borrarFiltroColumnaActual() {
    if (colActualFiltro!== null && tablaActualFiltro) {
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

    const dropdownReemplazo = document.getElementById("dropdownReemplazoMaterial");
    const inputReemplazo = document.getElementById("inputBuscarReemplazoMaterial");
    if (dropdownReemplazo && !dropdownReemplazo.classList.contains("hidden")) {
        if (!dropdownReemplazo.contains(e.target) && e.target !== inputReemplazo) {
            cerrarDropdownReemplazo();
        }
    }
});

// =========================================================================
// MODAL: EDITAR / CORREGIR MATERIAL DEL PROYECTO (BALANCE Y ACCIONES DIRECTAS)
// =========================================================================
let balanceMaterialesData = [];

function cargarBalanceMaterialesData() {
    const script = document.getElementById("balanceMaterialesModalJson");
    if (script && balanceMaterialesData.length === 0) {
        try {
            const raw = JSON.parse(script.textContent || "[]");
            if (Array.isArray(raw)) {
                balanceMaterialesData = raw;
            } else if (raw && typeof raw === "object") {
                balanceMaterialesData = Object.values(raw);
            } else {
                balanceMaterialesData = [];
            }
        } catch (e) {
            console.error("Error parseando balanceMaterialesModalJson:", e);
            balanceMaterialesData = [];
        }
    }
}

function abrirModalEditarMaterialBalance(materialId) {
    cargarCatalogoMateriales();
    cargarBalanceMaterialesData();

    const m = document.getElementById("modalEditarMaterialBalance");
    if (!m) return;

    // Buscar el material en balanceMaterialesData (soporta array u objeto)
    let item = null;
    if (Array.isArray(balanceMaterialesData)) {
        item = balanceMaterialesData.find(function (b) {
            return String(b.id) === String(materialId);
        });
    } else if (balanceMaterialesData && typeof balanceMaterialesData === "object") {
        item = balanceMaterialesData[materialId] || balanceMaterialesData[String(materialId)];
    }

    // Si no está en balanceMaterialesData, buscarlo en catalogoMateriales
    if (!item) {
        const cat = catalogoMateriales.find(function (c) {
            return String(c.id) === String(materialId);
        });
        if (cat) {
            item = {
                id: cat.id,
                item: cat.item,
                descripcion: cat.descripcion,
                unidad: cat.unidad,
                cantidad_requerida: 0,
                requerido: 0,
                cantidad_instalada: 0,
                instalado: 0,
                cantidad_retirada: 0,
                cantidad_entrada: 0,
                entrada: 0,
                tiene_requerido: false,
                req_id: null,
                instalados_detalles: [],
                entradas_detalles: []
            };
        }
    }

    if (!item) {
        alert("No se encontró la información del material seleccionado.");
        return;
    }

    // Cabecera
    const lblTitulo = document.getElementById("lblEditarMatTitulo");
    if (lblTitulo) {
        const cod = item.item ? `[${item.item}] ` : "";
        lblTitulo.textContent = `${cod}${item.descripcion} — Unidad: ${item.unidad || "UN"}`;
    }

    // CSRF token de la página
    const csrfTokenEl = document.querySelector("#formEditarRequeridoBalance [name=csrfmiddlewaretoken]");
    const csrfToken = csrfTokenEl ? csrfTokenEl.value : "";

    // SECCIÓN 1: REQUERIDO GENERAL
    const inputReqId = document.getElementById("inputEditReqId");
    const inputReqMatId = document.getElementById("inputEditReqMaterialId");
    const inputNuevoMatId = document.getElementById("inputEditNuevoMaterialId");
    const inputCant = document.getElementById("inputEditReqCantidad");
    const lblUnidad = document.getElementById("lblEditReqUnidad");
    const badgeReq = document.getElementById("badgeEstadoRequerido");
    const btnEliminar = document.getElementById("btnEliminarReqDirecto");
    const sinReqInfo = document.getElementById("sinRequeridoInfo");
    const inputElimReqId = document.getElementById("inputEliminarReqId");
    const inputElimMatId = document.getElementById("inputEliminarMaterialId");

    if (inputReqMatId) inputReqMatId.value = item.id;
    if (inputElimMatId) inputElimMatId.value = item.id;
    if (lblUnidad) lblUnidad.textContent = item.unidad || "UN";

    cancelarReemplazoMaterial();

    const cantReqVal = (item.cantidad_requerida !== undefined && item.cantidad_requerida !== null)
        ? item.cantidad_requerida
        : (item.requerido !== undefined && item.requerido !== null ? item.requerido : 0);

    if (item.tiene_requerido && item.req_id) {
        if (inputReqId) inputReqId.value = item.req_id;
        if (inputElimReqId) inputElimReqId.value = item.req_id;
        if (inputCant) inputCant.value = cantReqVal;
        if (badgeReq) {
            badgeReq.textContent = `Registrado (${cantReqVal} ${item.unidad || "UN"})`;
            badgeReq.className = "px-2 py-0.5 rounded text-[11px] font-bold bg-blue-100 text-blue-800 border border-blue-200";
        }
        if (btnEliminar) btnEliminar.classList.remove("hidden");
        if (sinReqInfo) sinReqInfo.classList.add("hidden");
    } else {
        if (inputReqId) inputReqId.value = "";
        if (inputElimReqId) inputElimReqId.value = "";
        if (inputCant) inputCant.value = "0";
        if (badgeReq) {
            badgeReq.textContent = "No registrado como Requerido directo";
            badgeReq.className = "px-2 py-0.5 rounded text-[11px] font-bold bg-slate-100 text-slate-600 border border-slate-200";
        }
        if (btnEliminar) btnEliminar.classList.add("hidden");
        if (sinReqInfo) sinReqInfo.classList.remove("hidden");
    }

    // SECCIÓN 2: INSTALADO EN APOYOS (INGENIERÍA)
    const listaApoyos = document.getElementById("listaApoyosInstalados");
    const sinApoyos = document.getElementById("sinApoyosInfo");
    const contApoyos = document.getElementById("contadorApoyosInstalados");

    const instList = item.instalados_detalles || [];
    if (contApoyos) {
        contApoyos.textContent = `${instList.length} apoyo(s)`;
    }

    if (instList.length > 0) {
        if (sinApoyos) sinApoyos.classList.add("hidden");
        if (listaApoyos) {
            listaApoyos.innerHTML = instList.map(function (ap) {
                const urlIng = `/ingenieria/proyectos/${item.proyecto_id || window.location.pathname.split("/")[3]}/?tab=materiales&editar_apoyo=${ap.apoyo_id}`;
                return `
                    <div class="p-3 bg-indigo-50/50 border border-indigo-100 rounded-lg flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                        <div class="space-y-0.5">
                            <p class="font-bold text-slate-900 text-xs flex items-center gap-1.5">
                                <span class="size-2 rounded-full bg-indigo-500"></span>
                                Apoyo / Poste: <span class="font-black text-indigo-900 text-sm">${ap.nodo || ("ID " + ap.apoyo_id)}</span>
                            </p>
                            <p class="text-[11px] text-slate-500">
                                Instalado actual: <strong class="text-slate-700">${ap.cantidad_instalada}</strong> ${item.unidad || "UN"}
                                ${ap.cantidad_retirada > 0 ? `· Retirado: <strong class="text-amber-700">${ap.cantidad_retirada}</strong>` : ""}
                            </p>
                        </div>

                        <div class="flex items-center gap-2 flex-wrap">
                            <!-- Formulario inline para cambiar cantidad instalada en este apoyo -->
                            <form method="POST" action="" class="flex items-center gap-1.5">
                                <input type="hidden" name="csrfmiddlewaretoken" value="${csrfToken}">
                                <input type="hidden" name="accion" value="editar_instalado_apoyo">
                                <input type="hidden" name="apoyo_material_id" value="${ap.id}">
                                <input type="number" step="any" min="0" name="cantidad_requerida" value="${ap.cantidad_instalada}"
                                       class="w-20 border border-indigo-200 rounded px-2 py-1 text-xs font-black text-slate-900 bg-white text-right focus:border-indigo-600 focus:outline-none"
                                       title="Editar cantidad instalada en este apoyo">
                                <button type="submit"
                                        class="px-2.5 py-1 bg-indigo-600 hover:bg-indigo-700 text-white rounded text-xs font-bold shadow-xs transition cursor-pointer"
                                        title="Guardar nueva cantidad instalada">
                                    Guardar
                                </button>
                            </form>

                            <!-- Formulario para quitar este material del apoyo -->
                            <form method="POST" action="" onsubmit="return confirm('¿Quitar este material de este apoyo?')" class="inline">
                                <input type="hidden" name="csrfmiddlewaretoken" value="${csrfToken}">
                                <input type="hidden" name="accion" value="eliminar_instalado_apoyo">
                                <input type="hidden" name="apoyo_material_id" value="${ap.id}">
                                <button type="submit"
                                        class="px-2.5 py-1 bg-rose-50 hover:bg-rose-100 text-rose-700 border border-rose-200 rounded text-xs font-bold transition cursor-pointer"
                                        title="Retirar material de este apoyo">
                                    ✕ Quitar
                                </button>
                            </form>

                            <!-- Enlace a la vista técnica en Ingeniería -->
                            <a href="${urlIng}" target="_blank"
                               class="px-2.5 py-1 bg-slate-200 hover:bg-slate-300 text-slate-700 rounded text-xs font-bold transition inline-flex items-center gap-1"
                               title="Abrir este apoyo en el módulo de Ingeniería">
                                <span>Abrir Apoyo</span>
                                <svg class="size-3" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M13.5 6H5.25A2.25 2.25 0 003 8.25v10.5A2.25 2.25 0 005.25 21h10.5A2.25 2.25 0 0018 18.75V10.5m-10.5 6L21 3m0 0h-5.25M21 3v5.25"/></svg>
                            </a>
                        </div>
                    </div>
                `;
            }).join("");
        }
    } else {
        if (listaApoyos) listaApoyos.innerHTML = "";
        if (sinApoyos) sinApoyos.classList.remove("hidden");
    }

    // SECCIÓN 3: ENTRADAS / REMISIONES
    const listaEntradas = document.getElementById("listaEntradasRemisiones");
    const sinEntradas = document.getElementById("sinEntradasInfo");
    const contEntradas = document.getElementById("contadorEntradasRemisiones");

    const entList = item.entradas_detalles || [];
    if (contEntradas) {
        contEntradas.textContent = `${entList.length} remisión(es)`;
    }

    if (entList.length > 0) {
        if (sinEntradas) sinEntradas.classList.add("hidden");
        if (listaEntradas) {
            listaEntradas.innerHTML = entList.map(function (ent) {
                const urlEditarEntrada = `/logistica/entradas/${ent.entrada_id}/editar/`;
                return `
                    <div class="p-3 bg-emerald-50/50 border border-emerald-100 rounded-lg flex items-center justify-between gap-3">
                        <div class="space-y-0.5">
                            <p class="font-bold text-slate-900 text-xs flex items-center gap-1.5">
                                <span class="size-2 rounded-full bg-emerald-500"></span>
                                Remisión: <span class="font-black text-emerald-900 text-sm font-mono">${ent.remision || "S/R"}</span>
                                ${ent.fecha ? `<span class="text-slate-400 font-normal">(${ent.fecha})</span>` : ""}
                            </p>
                            <p class="text-[11px] text-slate-500">
                                Cantidad recibida en remisión: <strong class="text-slate-800">${ent.cantidad}</strong> ${item.unidad || "UN"}
                            </p>
                        </div>

                        <div>
                            <a href="${urlEditarEntrada}"
                               class="px-3 py-1.5 bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg text-xs font-bold shadow-xs transition inline-flex items-center gap-1 cursor-pointer"
                               title="Editar cantidades o materiales registrados en esta remisión">
                                <svg class="size-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M16.862 4.487l1.687-1.688a1.875 1.875 0 112.652 2.652L10.582 16.07a4.5 4.5 0 01-1.897 1.13L6 18l.8-2.685a4.5 4.5 0 011.13-1.897l8.932-8.931zm0 0L19.5 7.125M18 14v4.75A2.25 2.25 0 0115.75 21H5.25A2.25 2.25 0 013 18.75V8.25A2.25 2.25 0 015.25 6H10"/></svg>
                                <span>Ver / Editar Remisión</span>
                            </a>
                        </div>
                    </div>
                `;
            }).join("");
        }
    } else {
        if (listaEntradas) listaEntradas.innerHTML = "";
        if (sinEntradas) sinEntradas.classList.remove("hidden");
    }

    m.classList.remove("hidden");
    m.classList.add("flex");
}

function cerrarModalEditarMaterialBalance() {
    const m = document.getElementById("modalEditarMaterialBalance");
    if (m) {
        m.classList.add("hidden");
        m.classList.remove("flex");
    }
    cerrarDropdownReemplazo();
}

function cerrarDropdownReemplazo() {
    const dropdown = document.getElementById("dropdownReemplazoMaterial");
    if (dropdown) {
        dropdown.classList.add("hidden");
        dropdown.innerHTML = "";
    }
}

function seleccionarMaterialReemplazo(mat) {
    const inputBuscar = document.getElementById("inputBuscarReemplazoMaterial");
    const hiddenNuevoId = document.getElementById("inputEditNuevoMaterialId");
    const alerta = document.getElementById("alertaReemplazoActivo");
    const textoAlerta = document.getElementById("textoReemplazoActivo");
    const btnCancelar = document.getElementById("btnCancelarReemplazo");

    if (hiddenNuevoId) hiddenNuevoId.value = mat.id;
    if (inputBuscar) inputBuscar.value = (mat.item ? `[${mat.item}] ` : "") + mat.descripcion;
    if (textoAlerta) {
        textoAlerta.innerHTML = `Cambiar por: <strong>${(mat.item ? `[${mat.item}] ` : '') + mat.descripcion}</strong> (${mat.unidad || 'UN'})`;
    }
    if (alerta) alerta.classList.remove("hidden");
    if (btnCancelar) btnCancelar.classList.remove("hidden");

    cerrarDropdownReemplazo();
}

function cancelarReemplazoMaterial() {
    const inputBuscar = document.getElementById("inputBuscarReemplazoMaterial");
    const hiddenNuevoId = document.getElementById("inputEditNuevoMaterialId");
    const alerta = document.getElementById("alertaReemplazoActivo");
    const btnCancelar = document.getElementById("btnCancelarReemplazo");

    if (hiddenNuevoId) hiddenNuevoId.value = "";
    if (inputBuscar) inputBuscar.value = "";
    if (alerta) alerta.classList.add("hidden");
    if (btnCancelar) btnCancelar.classList.add("hidden");
    cerrarDropdownReemplazo();
}

function confirmarEliminarRequerido() {
    if (!confirm("¿Estás seguro de que deseas eliminar este material de los requeridos del proyecto?")) {
        return;
    }
    const form = document.getElementById("formEliminarRequeridoBalance");
    if (form) form.submit();
}

// Modal de edición rápida de apoyo instalado (Tab 3)
function abrirModalEditarInstaladoRapido(id, nodo, desc, cant) {
    const m = document.getElementById("modalEditarInstaladoRapido");
    const inputId = document.getElementById("rapidoApoyoMaterialId");
    const lblNodo = document.getElementById("rapidoApoyoNodo");
    const lblDesc = document.getElementById("rapidoApoyoMaterialDesc");
    const inputCant = document.getElementById("rapidoApoyoCantidad");

    if (inputId) inputId.value = id;
    if (lblNodo) lblNodo.textContent = `Apoyo: ${nodo || '—'}`;
    if (lblDesc) lblDesc.textContent = `Material: ${desc || '—'}`;
    if (inputCant) inputCant.value = cant;

    if (m) {
        m.classList.remove("hidden");
        m.classList.add("flex");
        if (inputCant) {
            setTimeout(function () {
                inputCant.focus();
                inputCant.select();
            }, 100);
        }
    }
}

function cerrarModalEditarInstaladoRapido() {
    const m = document.getElementById("modalEditarInstaladoRapido");
    if (m) {
        m.classList.add("hidden");
        m.classList.remove("flex");
    }
}

// Autocomplete para el campo de búsqueda de reemplazo
document.addEventListener("DOMContentLoaded", function () {
    const inputReemplazo = document.getElementById("inputBuscarReemplazoMaterial");
    const dropdownReemplazo = document.getElementById("dropdownReemplazoMaterial");

    if (inputReemplazo && dropdownReemplazo) {
        inputReemplazo.addEventListener("input", function () {
            const query = normalizarTexto(inputReemplazo.value);
            if (query.length < 1) {
                cerrarDropdownReemplazo();
                return;
            }

            cargarCatalogoMateriales();
            const resultados = buscarMaterialesPriorizados(query, catalogoMateriales);

            if (resultados.length === 0) {
                dropdownReemplazo.innerHTML = `
                    <div class="px-4 py-3 text-xs text-slate-400 text-center">
                        No se encontraron materiales que coincidan con "<strong>${inputReemplazo.value}</strong>"
                    </div>
                `;
                dropdownReemplazo.classList.remove("hidden");
                return;
            }

            dropdownReemplazo.innerHTML = resultados.map(function (m, idx) {
                return `
                    <div class="px-3.5 py-2 hover:bg-amber-50 cursor-pointer flex items-center justify-between gap-2 item-sugerencia-reemplazo transition"
                         data-idx="${idx}">
                        <div class="flex items-center gap-2 truncate">
                            <span class="font-mono font-bold text-xs px-1.5 py-0.5 rounded bg-slate-100 text-slate-700 shrink-0">${m.item || "S/C"}</span>
                            <span class="font-semibold text-xs text-slate-900 truncate">${m.descripcion}</span>
                        </div>
                        <span class="text-[11px] font-black px-2 py-0.5 rounded bg-amber-100 text-amber-900 shrink-0 border border-amber-200">
                            ${m.unidad || "UN"}
                        </span>
                    </div>
                `;
            }).join("");

            dropdownReemplazo.querySelectorAll(".item-sugerencia-reemplazo").forEach(function (el, idx) {
                el.addEventListener("click", function () {
                    seleccionarMaterialReemplazo(resultados[idx]);
                });
            });

            dropdownReemplazo.classList.remove("hidden");
        });
    }
});
