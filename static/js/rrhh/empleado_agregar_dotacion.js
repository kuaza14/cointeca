/**
 * COINTECA S.A.S. - Módulo de Recursos Humanos
 * empleado_agregar_dotacion.js - Adición interactiva de dotaciones al empleado y control de cantidades.
 */

const elementos = {

    terreno: [
        "Botas de seguridad dieléctricas",
        "Camisa drill azul",
        "Casco de seguridad",
        "Monja",
        "Pantalón jean azul"
    ],

    administracion: [
        "Botas de seguridad dieléctricas",
        "Camibuzo",
        "Casco de seguridad",
        "Pantalón jean azul"
    ]
};

document.getElementById('tipoPersonal').addEventListener('change', function() {

    let tipo = this.value;

    let select = document.getElementById('elemento');

    select.innerHTML = '<option value="">Seleccione</option>';

    elementos[tipo].forEach(function(item) {

        select.innerHTML += `
            <option value="${item}">
                ${item}
            </option>
        `;

    });

});

function agregarElemento() {

    let elemento = document.getElementById('elemento').value;

    let descripcion = document.getElementById('descripcion').value;

    if(elemento === '') {

        alert('Seleccione un elemento');

        return;

    }

    let tabla = document.getElementById('tablaElementos');

    tabla.innerHTML += `

        <tr class="border-b">

            <td class="p-2">
                ${elemento}

                <input
                    type="hidden"
                    name="elementos[]"
                    value="${elemento}"
                >
            </td>

            <td class="p-2">
                ${descripcion}

                <input
                    type="hidden"
                    name="descripciones[]"
                    value="${descripcion}"
                >
            </td>

            <td class="p-2 text-center">

                <button
                    type="button"
                    onclick="this.parentElement.parentElement.remove()"
                    class="bg-destructive text-white px-3 py-1 rounded text-sm"
                >
                    Eliminar
                </button>

            </td>

        </tr>

    `;

    document.getElementById('descripcion').value = '';

}
