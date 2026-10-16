/**
 * COINTECA S.A.S. - Módulo de Logística
 * materiales_requeridos.js - Gestión dinámica de requisiciones de material con buscador predictivo y adición rápida.
 */

let catalogoMaterialesReq = [];
let itemsAgregados = [];
let indiceSugerenciaActivaReq = -1;

function abrirModalAgregar() {
    cargarCatalogoMaterialesReq();
    const modal = document.getElementById("modalAgregarRequerido");
    if (modal) {
        modal.classList.remove("hidden");
        modal.classList.add("flex");
        modal.style.display = "flex";
        setTimeout(function () {
            const inp = document.getElementById("inputBuscadorMaterialModalReq");
            if (inp) inp.focus();
        }, 100);
    }
}

function cerrarModalAgregar() {
    const modal = document.getElementById("modalAgregarRequerido");
    if (modal) {
        modal.classList.add("hidden");
        modal.classList.remove("flex");
        modal.style.display = "none";
        cerrarDropdownSugerenciasReq();
    }
}

function cerrarDropdownSugerenciasReq() {
    const dropdown = document.getElementById("dropdownSugerenciasMaterialReq");
    if (dropdown) {
        dropdown.classList.add("hidden");
        dropdown.innerHTML = "";
    }
    indiceSugerenciaActivaReq = -1;
}

function normalizarTextoReq(txt) {
    if (!txt) return "";
    return txt.toString().toLowerCase().normalize("NFD").replace(/[\u0300-\u036f]/g, "").trim();
}

function cargarCatalogoMaterialesReq() {
    const script = document.getElementById("catalogoMaterialesDataReq");
    if (script && catalogoMaterialesReq.length === 0) {
        try {
            catalogoMaterialesReq = JSON.parse(script.textContent || "[]");
        } catch (e) {
            console.error("Error parseando catálogo de materiales:", e);
        }
    }
}

function seleccionarMaterialModalReq(mat) {
    const inputBuscador = document.getElementById("inputBuscadorMaterialModalReq");
    const btnLimpiar = document.getElementById("btnLimpiarMaterialModalReq");
    const hiddenId = document.getElementById("modalSelMaterialIdReq");
    const hiddenItem = document.getElementById("modalSelMaterialItemReq");
    const hiddenDesc = document.getElementById("modalSelMaterialDescReq");
    const hiddenUnidad = document.getElementById("modalSelMaterialUnidadReq");
    const badgeUnidad = document.getElementById("badgeUnidadModalReq");
    const textoUnidad = document.getElementById("textoUnidadModalReq");
    const inputCantidad = document.getElementById("inputCantidadModal");

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

    cerrarDropdownSugerenciasReq();

    if (inputCantidad) {
        inputCantidad.focus();
        inputCantidad.select();
    }
}

function limpiarSeleccionMaterialModalReq() {
    const inputBuscador = document.getElementById("inputBuscadorMaterialModalReq");
    const btnLimpiar = document.getElementById("btnLimpiarMaterialModalReq");
    const hiddenId = document.getElementById("modalSelMaterialIdReq");
    const hiddenItem = document.getElementById("modalSelMaterialItemReq");
    const hiddenDesc = document.getElementById("modalSelMaterialDescReq");
    const hiddenUnidad = document.getElementById("modalSelMaterialUnidadReq");
    const badgeUnidad = document.getElementById("badgeUnidadModalReq");
    const textoUnidad = document.getElementById("textoUnidadModalReq");
    const inputCantidad = document.getElementById("inputCantidadModal");

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
    cerrarDropdownSugerenciasReq();
    if (inputBuscador) inputBuscador.focus();
}

function agregarMaterialALista() {
    const hiddenId = document.getElementById("modalSelMaterialIdReq");
    const hiddenItem = document.getElementById("modalSelMaterialItemReq");
    const hiddenDesc = document.getElementById("modalSelMaterialDescReq");
    const hiddenUnidad = document.getElementById("modalSelMaterialUnidadReq");
    const inputCantidad = document.getElementById("inputCantidadModal");
    const inputBuscador = document.getElementById("inputBuscadorMaterialModalReq");

    const materialId = hiddenId ? hiddenId.value : "";
    if (!materialId) {
        alert("Por favor selecciona un material del catálogo.");
        if (inputBuscador) inputBuscador.focus();
        return;
    }

    const cantidadStr = inputCantidad ? inputCantidad.value.trim().replace(",", ".") : "";
    const cantNum = parseFloat(cantidadStr);
    if (isNaN(cantNum) || cantNum <= 0) {
        alert("Por favor ingresa una cantidad válida mayor a 0.");
        if (inputCantidad) inputCantidad.focus();
        return;
    }

    const itemCode = hiddenItem ? hiddenItem.value : "";
    const desc = hiddenDesc ? hiddenDesc.value : "";
    const unidad = hiddenUnidad ? hiddenUnidad.value : "UN";

    const existente = itemsAgregados.find(function (it) {
        return String(it.material_id) === String(materialId);
    });

    if (existente) {
        existente.cantidad += cantNum;
    } else {
        itemsAgregados.push({
            material_id: materialId,
            item: itemCode,
            descripcion: desc,
            unidad: unidad,
            cantidad: cantNum
        });
    }

    renderizarTablaModal();
    limpiarSeleccionMaterialModalReq();
}

function eliminarItemModal(index) {
    itemsAgregados.splice(index, 1);
    renderizarTablaModal();
}

function renderizarTablaModal() {
    const tbody = document.getElementById("cuerpoTablaModal");
    const contador = document.getElementById("contadorItemsLista");
    const btnGuardar = document.getElementById("btnGuardarModal");
    if (!tbody) return;

    if (contador) {
        const n = itemsAgregados.length;
        contador.textContent = n + (n === 1 ? " material" : " materiales");
    }

    if (itemsAgregados.length === 0) {
        tbody.innerHTML = `
            <tr id="filaVaciaModal">
                <td colspan="5" class="px-4 py-8 text-center text-gray-400 text-xs">
                    <div class="space-y-1">
                        <p class="font-bold text-gray-600 text-sm">Aún no has agregado materiales a la lista.</p>
                        <p class="text-gray-400">Busca el material arriba, digita la cantidad y haz clic en <strong>"+ Agregar"</strong>.</p>
                    </div>
                </td>
            </tr>
        `;
        if (btnGuardar) btnGuardar.disabled = true;
        return;
    }

    if (btnGuardar) btnGuardar.disabled = false;

    tbody.innerHTML = itemsAgregados.map(function (it, idx) {
        const cantFormatted = it.cantidad % 1 === 0 ? it.cantidad : it.cantidad.toFixed(2);
        return `
            <tr class="hover:bg-blue-50/50 transition">
                <td class="px-3 py-2.5 text-center font-mono text-xs font-bold text-gray-600">
                    ${it.item || "—"}
                    <input type="hidden" name="material_id[]" value="${it.material_id}">
                </td>
                <td class="px-4 py-2.5 font-semibold text-gray-900 text-xs">
                    ${it.descripcion}
                </td>
                <td class="px-3 py-2.5 text-center text-xs font-bold text-gray-600">
                    <span class="px-2 py-0.5 rounded bg-blue-100 text-blue-900 border border-blue-200">${it.unidad}</span>
                </td>
                <td class="px-4 py-2.5 text-right font-black text-blue-900 text-sm">
                    ${cantFormatted}
                    <input type="hidden" name="cantidad[]" value="${it.cantidad}">
                </td>
                <td class="px-3 py-2.5 text-center">
                    <button type="button" onclick="eliminarItemModal(${idx})"
                            class="text-red-500 hover:text-red-700 hover:bg-red-50 p-1 rounded transition text-base font-black cursor-pointer leading-none"
                            title="Quitar de la lista">
                        &times;
                    </button>
                </td>
            </tr>
        `;
    }).join("");
}

function buscarMaterialesPriorizadosReq(query, catalogo) {
    const qNorm = normalizarTextoReq(query);
    if (!qNorm) return [];

    const palabras = qNorm.split(/\s+/).filter(p => p.length > 0);
    const resultadosScored = [];

    for (let i = 0; i < catalogo.length; i++) {
        const m = catalogo[i];
        const itemNorm = normalizarTextoReq(m.item);
        const descNorm = normalizarTextoReq(m.descripcion);
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

// Inicialización de Event Listeners
document.addEventListener("DOMContentLoaded", function () {
    cargarCatalogoMaterialesReq();

    const inputBuscadorReq = document.getElementById("inputBuscadorMaterialModalReq");
    const dropdownReq = document.getElementById("dropdownSugerenciasMaterialReq");
    const btnLimpiarReq = document.getElementById("btnLimpiarMaterialModalReq");
    const inputCantidadReq = document.getElementById("inputCantidadModal");
    const modalReq = document.getElementById("modalAgregarRequerido");

    if (inputBuscadorReq && dropdownReq) {
        inputBuscadorReq.addEventListener("input", function () {
            const query = normalizarTextoReq(inputBuscadorReq.value);
            if (btnLimpiarReq) {
                if (inputBuscadorReq.value.trim().length > 0) {
                    btnLimpiarReq.classList.remove("hidden");
                } else {
                    btnLimpiarReq.classList.add("hidden");
                }
            }

            if (query.length < 1) {
                cerrarDropdownSugerenciasReq();
                return;
            }

            cargarCatalogoMaterialesReq();
            const resultados = buscarMaterialesPriorizadosReq(query, catalogoMaterialesReq);

            if (resultados.length === 0) {
                dropdownReq.innerHTML = `
                    <div class="px-4 py-3 text-xs text-slate-400 text-center">
                        No se encontraron materiales que coincidan con "<strong>${inputBuscadorReq.value}</strong>"
                    </div>
                `;
                dropdownReq.classList.remove("hidden");
                return;
            }

            dropdownReq.innerHTML = resultados.map(function (m, idx) {
                return `
                    <div class="px-3.5 py-2.5 hover:bg-blue-50 cursor-pointer flex items-center justify-between gap-2 item-sugerencia-material-req transition"
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

            dropdownReq.querySelectorAll(".item-sugerencia-material-req").forEach(function (el, idx) {
                el.addEventListener("click", function () {
                    seleccionarMaterialModalReq(resultados[idx]);
                });
            });

            indiceSugerenciaActivaReq = -1;
            dropdownReq.classList.remove("hidden");
        });

        inputBuscadorReq.addEventListener("keydown", function (e) {
            const items = dropdownReq.querySelectorAll(".item-sugerencia-material-req");
            if (!dropdownReq.classList.contains("hidden") && items.length > 0) {
                if (e.key === "ArrowDown") {
                    e.preventDefault();
                    indiceSugerenciaActivaReq = (indiceSugerenciaActivaReq + 1) % items.length;
                    actualizarResaltadoReq(items);
                    return;
                }
                if (e.key === "ArrowUp") {
                    e.preventDefault();
                    indiceSugerenciaActivaReq = (indiceSugerenciaActivaReq - 1 + items.length) % items.length;
                    actualizarResaltadoReq(items);
                    return;
                }
                if (e.key === "Enter") {
                    e.preventDefault();
                    if (indiceSugerenciaActivaReq >= 0 && indiceSugerenciaActivaReq < items.length) {
                        items[indiceSugerenciaActivaReq].click();
                    } else if (items.length > 0) {
                        items[0].click();
                    }
                    return;
                }
                if (e.key === "Escape") {
                    cerrarDropdownSugerenciasReq();
                    return;
                }
            }
        });
    }

    function actualizarResaltadoReq(items) {
        items.forEach((it, idx) => {
            if (idx === indiceSugerenciaActivaReq) {
                it.classList.add("bg-blue-100");
                it.scrollIntoView({ block: "nearest" });
            } else {
                it.classList.remove("bg-blue-100");
            }
        });
    }

    if (btnLimpiarReq) {
        btnLimpiarReq.addEventListener("click", limpiarSeleccionMaterialModalReq);
    }

    if (inputCantidadReq) {
        inputCantidadReq.addEventListener("keydown", function (e) {
            if (e.key === "Enter") {
                e.preventDefault();
                agregarMaterialALista();
            }
        });
    }

    if (modalReq) {
        modalReq.addEventListener("click", function (event) {
            if (event.target === modalReq) {
                cerrarModalAgregar();
            }
        });
    }

    document.addEventListener("click", function (e) {
        if (dropdownReq && !dropdownReq.contains(e.target) && e.target !== inputBuscadorReq) {
            cerrarDropdownSugerenciasReq();
        }
    });

    // Buscador en vivo de la tabla principal de materiales requeridos
    const inputBuscadorPrincipal = document.getElementById("buscadorRequeridos");
    const btnLimpiarPrincipal = document.getElementById("btnLimpiarRequeridos");
    const contadorPrincipal = document.getElementById("contadorRequeridosVisible");
    const filasPrincipal = document.querySelectorAll(".fila-requerido-tabla");

    function filtrarRequeridosPrincipal() {
        const q = inputBuscadorPrincipal ? inputBuscadorPrincipal.value.toLowerCase().trim() : "";

        if (btnLimpiarPrincipal) {
            if (q.length > 0) {
                btnLimpiarPrincipal.classList.remove("hidden");
                btnLimpiarPrincipal.classList.add("flex");
            } else {
                btnLimpiarPrincipal.classList.add("hidden");
                btnLimpiarPrincipal.classList.remove("flex");
            }
        }

        let visibles = 0;
        filasPrincipal.forEach(function (fila) {
            const texto = fila.textContent.toLowerCase();
            const match = (q === "" || texto.includes(q));
            fila.style.display = match ? "" : "none";
            if (match) visibles++;
        });

        if (contadorPrincipal) {
            contadorPrincipal.textContent = visibles;
        }
    }

    if (inputBuscadorPrincipal) {
        inputBuscadorPrincipal.addEventListener("input", filtrarRequeridosPrincipal);
        inputBuscadorPrincipal.addEventListener("keydown", function (e) {
            if (e.key === "Escape") {
                inputBuscadorPrincipal.value = "";
                filtrarRequeridosPrincipal();
            }
        });
    }

    if (btnLimpiarPrincipal) {
        btnLimpiarPrincipal.addEventListener("click", function () {
            if (inputBuscadorPrincipal) {
                inputBuscadorPrincipal.value = "";
                filtrarRequeridosPrincipal();
                inputBuscadorPrincipal.focus();
            }
        });
    }

    // Buscador interactivo de reemplazo de material
    const inputReemplazoDir = document.getElementById("editDirInputBuscarReemplazo");
    const dropdownReemplazoDir = document.getElementById("editDirDropdownReemplazo");

    if (inputReemplazoDir && dropdownReemplazoDir) {
        inputReemplazoDir.addEventListener("input", function () {
            const query = normalizarTextoReq(inputReemplazoDir.value);
            if (query.length < 1) {
                cerrarDropdownReemplazoDirecto();
                return;
            }

            cargarCatalogoMaterialesReq();
            const resultados = buscarMaterialesPriorizadosReq(query, catalogoMaterialesReq);

            if (resultados.length === 0) {
                dropdownReemplazoDir.innerHTML = `
                    <div class="px-4 py-3 text-xs text-slate-400 text-center">
                        No se encontraron materiales que coincidan con "<strong>${inputReemplazoDir.value}</strong>"
                    </div>
                `;
                dropdownReemplazoDir.classList.remove("hidden");
                return;
            }

            dropdownReemplazoDir.innerHTML = resultados.map(function (m, idx) {
                return `
                    <div class="px-3.5 py-2 hover:bg-amber-50 cursor-pointer flex items-center justify-between gap-2 item-sugerencia-reemplazo-dir transition"
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

            dropdownReemplazoDir.querySelectorAll(".item-sugerencia-reemplazo-dir").forEach(function (el, idx) {
                el.addEventListener("click", function () {
                    seleccionarMaterialReemplazoDirecto(resultados[idx]);
                });
            });

            dropdownReemplazoDir.classList.remove("hidden");
        });
    }

    document.addEventListener("click", function (e) {
        if (dropdownReemplazoDir && !dropdownReemplazoDir.classList.contains("hidden")) {
            if (!dropdownReemplazoDir.contains(e.target) && e.target !== inputReemplazoDir) {
                cerrarDropdownReemplazoDirecto();
            }
        }
    });
});

// =========================================================================
// MODAL: EDITAR / CAMBIAR MATERIAL REQUERIDO DIRECTO
// =========================================================================
function abrirModalEditarRequeridoDirecto(targetOrReqId, matId, item, desc, unidad, cant) {
    let reqId = targetOrReqId;
    if (targetOrReqId && targetOrReqId.dataset) {
        const ds = targetOrReqId.dataset;
        reqId = ds.reqId;
        matId = ds.matId;
        item = ds.item || "";
        desc = ds.desc || "";
        unidad = ds.unidad || "UN";
        cant = ds.cantidad || "";
    }

    cargarCatalogoMaterialesReq();
    const modal = document.getElementById("modalEditarRequeridoDirecto");
    const inputReqId = document.getElementById("editDirReqId");
    const lblDesc = document.getElementById("editDirMaterialActualDesc");
    const lblInfo = document.getElementById("editDirMaterialActualInfo");
    const inputCant = document.getElementById("editDirCantidad");
    const lblUnidad = document.getElementById("editDirUnidad");

    if (inputReqId) inputReqId.value = reqId;
    if (lblDesc) lblDesc.textContent = (item ? `[${item}] ` : "") + desc;
    if (lblInfo) lblInfo.textContent = `Código: ${item || 'S/C'} · Unidad: ${unidad || 'UN'}`;
    if (inputCant) inputCant.value = cant;
    if (lblUnidad) lblUnidad.textContent = unidad || "UN";

    cancelarReemplazoMaterialDirecto();

    if (modal) {
        modal.classList.remove("hidden");
        modal.classList.add("flex");
        modal.style.display = "flex";
        if (inputCant) {
            setTimeout(function () {
                inputCant.focus();
                inputCant.select();
            }, 100);
        }
    }
}

function cerrarModalEditarRequeridoDirecto() {
    const modal = document.getElementById("modalEditarRequeridoDirecto");
    if (modal) {
        modal.classList.add("hidden");
        modal.classList.remove("flex");
        modal.style.display = "none";
    }
    cerrarDropdownReemplazoDirecto();
}

function cerrarDropdownReemplazoDirecto() {
    const dropdown = document.getElementById("editDirDropdownReemplazo");
    if (dropdown) {
        dropdown.classList.add("hidden");
        dropdown.innerHTML = "";
    }
}

function seleccionarMaterialReemplazoDirecto(mat) {
    const inputBuscar = document.getElementById("editDirInputBuscarReemplazo");
    const hiddenNuevoId = document.getElementById("editDirNuevoMaterialId");
    const alerta = document.getElementById("editDirAlertaReemplazo");
    const textoAlerta = document.getElementById("editDirTextoReemplazo");
    const btnCancelar = document.getElementById("editDirBtnCancelarReemplazo");

    if (hiddenNuevoId) hiddenNuevoId.value = mat.id;
    if (inputBuscar) inputBuscar.value = (mat.item ? `[${mat.item}] ` : "") + mat.descripcion;
    if (textoAlerta) {
        textoAlerta.innerHTML = `Cambiar por: <strong>${(mat.item ? `[${mat.item}] ` : '') + mat.descripcion}</strong> (${mat.unidad || 'UN'})`;
    }
    if (alerta) alerta.classList.remove("hidden");
    if (btnCancelar) btnCancelar.classList.remove("hidden");

    cerrarDropdownReemplazoDirecto();
}

function cancelarReemplazoMaterialDirecto() {
    const inputBuscar = document.getElementById("editDirInputBuscarReemplazo");
    const hiddenNuevoId = document.getElementById("editDirNuevoMaterialId");
    const alerta = document.getElementById("editDirAlertaReemplazo");
    const btnCancelar = document.getElementById("editDirBtnCancelarReemplazo");

    if (hiddenNuevoId) hiddenNuevoId.value = "";
    if (inputBuscar) inputBuscar.value = "";
    if (alerta) alerta.classList.add("hidden");
    if (btnCancelar) btnCancelar.classList.add("hidden");
    cerrarDropdownReemplazoDirecto();
}
