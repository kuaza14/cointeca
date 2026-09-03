function crearBuscador(inputId, selectorElementos) {
    const input = document.getElementById(inputId);

    // Si esta página no tiene ese buscador, no hacer nada
    if (!input) return;

    input.addEventListener('input', function () {
        const texto = input.value.toLowerCase().trim();
        const elementos = document.querySelectorAll(selectorElementos);

        elementos.forEach(function (elemento) {
            const contenido = elemento.textContent.toLowerCase();

            if (contenido.includes(texto)) {
                elemento.style.display = '';
            } else {
                elemento.style.display = 'none';
            }
        });
    });
}


document.addEventListener('DOMContentLoaded', function () {

    const buscarEmpleado = document.getElementById('buscarEmpleado');
    const resultadosEmpleados = document.getElementById('resultadosEmpleados');
    const empleadoSeleccionado = document.getElementById('empleadoSeleccionado');
    const opcionesEmpleados = document.querySelectorAll('.empleado-opcion');

    // Si esta página no tiene buscador de empleados, no hacemos nada.
    if (!buscarEmpleado) {
        return;
    }

    // ==========================================
    // BUSCAR EMPLEADO
    // ==========================================
    buscarEmpleado.addEventListener('input', function () {
        const texto = this.value.toLowerCase().trim();

        // Solo limpiamos el ID si el usuario vació por completo el campo de texto
        if (texto === '') {
            empleadoSeleccionado.value = '';
        }

        let hayResultados = false;

        opcionesEmpleados.forEach(function (opcion) {
            const nombre = opcion.dataset.nombre.toLowerCase();

            if (nombre.includes(texto)) {
                opcion.classList.remove('hidden');
                hayResultados = true;
            } else {
                opcion.classList.add('hidden');
            }
        });

        if (texto && hayResultados) {
            resultadosEmpleados.classList.remove('hidden');
        } else {
            resultadosEmpleados.classList.add('hidden');
        }
    });


    // ==========================================
    // SELECCIONAR EMPLEADO
    // ==========================================
    opcionesEmpleados.forEach(function (opcion) {
        opcion.addEventListener('click', function () {
            const nombre = this.dataset.nombre;
            const id = this.dataset.id;

            // Mostrar nombre
            buscarEmpleado.value = nombre;

            // Guardar ID REAL del empleado
            empleadoSeleccionado.value = id;

            // Ocultar resultados
            resultadosEmpleados.classList.add('hidden');

            console.log("Empleado seleccionado:");
            console.log("Nombre:", nombre);
            console.log("ID:", id);
        });
    });


    // ==========================================
    // MOSTRAR RESULTADOS AL HACER FOCUS
    // ==========================================
    buscarEmpleado.addEventListener('focus', function () {
        const texto = this.value.toLowerCase().trim();
        let hayResultados = false;

        opcionesEmpleados.forEach(function (opcion) {
            const nombre = opcion.dataset.nombre.toLowerCase();

            if (!texto || nombre.includes(texto)) {
                opcion.classList.remove('hidden');
                hayResultados = true;
            } else {
                opcion.classList.add('hidden');
            }
        });

        if (hayResultados) {
            resultadosEmpleados.classList.remove('hidden');
        }
    });


    // ==========================================
    // CERRAR AL HACER CLIC AFUERA
    // ==========================================
    document.addEventListener('click', function (e) {
        if (
            !buscarEmpleado.contains(e.target) &&
            !resultadosEmpleados.contains(e.target)
        ) {
            resultadosEmpleados.classList.add('hidden');
        }
    });

});