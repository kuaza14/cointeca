/**
 * COINTECA S.A.S. - Módulo de Recursos Humanos
 * inducciones_empleado.js - Modales para asignación y registro de capacitaciones.
 */

function confirmarEliminar(id) {

    document
        .getElementById('modalEliminar')
        .classList.remove('hidden')

    document
        .getElementById('formEliminar')
        .action = `/rrhh/inducciones/${id}/eliminar/`

}

function cerrarModal() {

    document
        .getElementById('modalEliminar')
        .classList.add('hidden')

}
