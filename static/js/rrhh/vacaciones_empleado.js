/**
 * COINTECA S.A.S. - Módulo de Recursos Humanos
 * vacaciones_empleado.js - Navegación por historial de vacaciones individuales.
 */

function abrirEditar(id, periodo, fecha_inicio, dias_tomados, observaciones) {
    if (typeof abrirEditarVacacion === "function") {
        abrirEditarVacacion(id, "Colaborador", periodo, fecha_inicio, dias_tomados, observaciones, 0, 0);
    }
}

function abrirEliminar(id) {
    if (typeof abrirEliminarVacacion === "function") {
        abrirEliminarVacacion(id, "Colaborador", 0);
    }
}
