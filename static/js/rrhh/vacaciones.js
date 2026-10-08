/**
 * COINTECA S.A.S. - Módulo de Recursos Humanos
 * vacaciones.js - Filtrado en vivo de solicitudes de vacaciones por estado y empleado.
 */

// EDITAR
        function abrirEditar(id, periodo, fecha_inicio, dias, observaciones){

            document.getElementById("modalEditar").classList.remove("hidden");

            document.getElementById("periodo").value = periodo;
            document.getElementById("fecha_inicio").value = fecha_inicio;
            document.getElementById("dias_tomados").value = dias;
            document.getElementById("observaciones").value = observaciones;

            document.getElementById("formEditar").action = "/rrhh/vacaciones/" + id + "/editar/";

        }

        function cerrarEditar(){
            document.getElementById("modalEditar").classList.add("hidden");
        }

        // ELIMINAR
        function abrirEliminar(id){

            document.getElementById("modalEliminar").classList.remove("hidden");

            document.getElementById("formEliminar").action = "/rrhh/vacaciones/" + id + "/eliminar/";

        }

        function cerrarEliminar(){
            document.getElementById("modalEliminar").classList.add("hidden");
        }
