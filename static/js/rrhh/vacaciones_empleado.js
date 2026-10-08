/**
 * COINTECA S.A.S. - Módulo de Recursos Humanos
 * vacaciones_empleado.js - Navegación por historial de vacaciones individuales.
 */

function abrirEditar(id, periodo, fecha_inicio, dias_tomados, observaciones) {
        // Aquí puedes implementar la lógica para abrir un modal o redirigir a una página de edición
        alert(`Editar vacaciones:\nID: ${id}\nPeriodo: ${periodo}\nInicio: ${fecha_inicio}\nDías tomados: ${dias_tomados}\nObservaciones: ${observaciones}`);
    }

    function abrirEliminar(id) {
        // Aquí puedes implementar la lógica para abrir un modal de confirmación o redirigir a una página de eliminación
        if (confirm(`¿Estás seguro de que deseas eliminar las vacaciones con ID: ${id}?`)) {
            // Redirigir a la URL de eliminación
            window.location.href = `/rrhh/vacaciones/${id}/eliminar/`;
        }
    }
