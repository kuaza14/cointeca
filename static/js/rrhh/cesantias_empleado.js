/**
 * COINTECA S.A.S. - Módulo de Recursos Humanos
 * cesantias_empleado.js - Validaciones de retiros de cesantías por colaborador.
 */

function confirmarEliminar(id) {
            document.getElementById('modalEliminar').classList.remove('hidden');
            document.getElementById('formEliminar').action = `/rrhh/cesantias/${id}/eliminar/`;
        }

        function cerrarModal() {
            document.getElementById('modalEliminar').classList.add('hidden');
        }
