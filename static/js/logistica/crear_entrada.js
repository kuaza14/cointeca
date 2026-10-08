/**
 * COINTECA S.A.S. - Módulo de Logística
 * crear_entrada.js - Adición dinámica de ítems de entrada de almacén, autocompletado y validaciones.
 */

document.addEventListener('DOMContentLoaded', function () {
    const campoFecha = document.getElementById('campoFecha');
    if (campoFecha && !campoFecha.value) {
        campoFecha.value = new Date().toISOString().split('T')[0];
    }
});

const tbody = document.getElementById('filasMateriales');
const btnAgregar = document.getElementById('btnAgregarFila');

if (btnAgregar) {
    btnAgregar.addEventListener('click', function () {
        agregarFila('', '');
    });
}

function agregarFila(matId, cantidad) {
    const filas = tbody.querySelectorAll('.fila-material');
    let filaVacia = null;
    filas.forEach(function (fila) {
        const select = fila.querySelector('.select-material');
        const input = fila.querySelector('.input-cantidad');
        if (select.value === '' && input.value === '') {
            filaVacia = fila;
        }
    });

    if (filaVacia && matId) {
        filaVacia.querySelector('.select-material').value = matId;
        filaVacia.querySelector('.input-cantidad').value = cantidad;
        return;
    }

    const plantilla = document.getElementById('plantillaFilaMaterial');
    let nuevaFila;
    if (plantilla) {
        nuevaFila = plantilla.content.firstElementChild.cloneNode(true);
    } else {
        const primeraFila = tbody.querySelector('.fila-material');
        if (!primeraFila) return;
        nuevaFila = primeraFila.cloneNode(true);
    }
    nuevaFila.querySelector('.select-material').value = matId || '';
    nuevaFila.querySelector('.input-cantidad').value = cantidad || '';
    tbody.appendChild(nuevaFila);
}

tbody.addEventListener('click', function (e) {
    if (e.target.classList.contains('btnEliminarFila')) {
        const filas = tbody.querySelectorAll('.fila-material');
        if (filas.length > 1) {
            e.target.closest('.fila-material').remove();
        } else {
            const fila = e.target.closest('.fila-material');
            fila.querySelector('.select-material').value = '';
            fila.querySelector('.input-cantidad').value = '';
        }
    }
});

function agregarMaterialDirecto(matId, cantidad) {
    agregarFila(matId, cantidad);
}

const requeridosData = JSON.parse(
    document.getElementById('requeridos-data').textContent
);

function cargarTodosLosPendientes() {
    if (!requeridosData || requeridosData.length === 0) {
        return;
    }

    tbody.innerHTML = '';
    const plantilla = document.getElementById('plantillaFilaMaterial');
    requeridosData.forEach(function (item) {
        let tr;
        if (plantilla) {
            tr = plantilla.content.firstElementChild.cloneNode(true);
        } else {
            return;
        }
        const select = tr.querySelector('.select-material');
        const input = tr.querySelector('.input-cantidad');
        if (select) select.value = item.material_id;
        if (input) input.value = item.cantidad;
        tbody.appendChild(tr);
    });
}

function editarDetalle(detalleId) {
    const fila = document.getElementById(
        'detalle-' + detalleId
    );
    if (!fila) {
        console.error('No se encontró el detalle:', detalleId);
        return;
    }
    const cantidadNormal = fila.querySelector(
        '.cantidad-normal'
    );
    const formularioEditar = fila.querySelector(
        '.form-editar-detalle'
    );
    const botonEditar = fila.querySelector(
        '.boton-editar-detalle'
    );
    const formularioEliminar = fila.querySelector(
        '.form-eliminar-detalle'
    );
    if (!formularioEditar) {
        console.error('No se encontró el formulario de edición');
        return;
    }
    // Ocultar cantidad normal
    cantidadNormal.classList.add('hidden');
    // Mostrar formulario de edición
    formularioEditar.classList.remove('hidden');
    // Ocultar botón editar
    botonEditar.classList.add('hidden');
    // Ocultar botón eliminar
    formularioEliminar.classList.add('hidden');
    // Enfocar el input
    const input = formularioEditar.querySelector(
        'input[name="cantidad"]'
    );
    input.focus();
    input.select();
}


function cancelarDetalle(detalleId) {
    const fila = document.getElementById(
        'detalle-' + detalleId
    );
    if (!fila) {
        return;
    }
    const cantidadNormal = fila.querySelector(
        '.cantidad-normal'
    );
    const formularioEditar = fila.querySelector(
        '.form-editar-detalle'
    );
    const botonEditar = fila.querySelector(
        '.boton-editar-detalle'
    );
    const formularioEliminar = fila.querySelector(
        '.form-eliminar-detalle'
    );
    cantidadNormal.classList.remove('hidden');
    formularioEditar.classList.add('hidden');
    botonEditar.classList.remove('hidden');
    formularioEliminar.classList.remove('hidden');
}
