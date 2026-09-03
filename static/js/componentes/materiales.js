    document.addEventListener('DOMContentLoaded', function () {
        const tbody = document.getElementById('filasNuevosMateriales');
        const btnAgregar = document.getElementById('btnAgregarFilaMaterial');

        btnAgregar.addEventListener('click', function () {
            const primeraFila = tbody.querySelector('.fila-nuevo-material');
            if (primeraFila) {
                const nuevaFila = primeraFila.cloneNode(true);
                // Limpiar valores
                const select = nuevaFila.querySelector('select[name="material_id[]"]');
                if (select) select.selectedIndex = 0;
                const inputCant = nuevaFila.querySelector('input[name="cantidad[]"]');
                if (inputCant) inputCant.value = '';
                const selectUnidad = nuevaFila.querySelector('select[name="unidad[]"]');
                if (selectUnidad) selectUnidad.selectedIndex = 0;

                tbody.appendChild(nuevaFila);
            }
        });

        tbody.addEventListener('click', function (e) {
            if (e.target.classList.contains('btnEliminarFila')) {
                const filas = tbody.querySelectorAll('.fila-nuevo-material');
                if (filas.length > 1) {
                    e.target.closest('.fila-nuevo-material').remove();
                } else {
                    // Si es la única, solo limpiar
                    const fila = e.target.closest('.fila-nuevo-material');
                    fila.querySelector('select[name="material_id[]"]').selectedIndex = 0;
                    fila.querySelector('input[name="cantidad[]"]').value = '';
                }
            }
        });

        // Cambiar unidad automáticamente si el material seleccionado tiene unidad configurada
        tbody.addEventListener('change', function(e) {
            if (e.target.name === 'material_id[]') {
                const selectedOption = e.target.options[e.target.selectedIndex];
                const unidad = selectedOption.getAttribute('data-unidad');
                const row = e.target.closest('.fila-nuevo-material');
                const selectUnidad = row.querySelector('select[name="unidad[]"]');

                if (unidad && selectUnidad) {
                    if (unidad.toUpperCase().startsWith('M')) {
                        selectUnidad.value = 'M';
                    } else if (unidad.toUpperCase().startsWith('U')) {
                        selectUnidad.value = 'U';
                    } else {
                        selectUnidad.value = 'U';
                    }
                }
            }
        });
    });

document.querySelectorAll('.btnEditarMaterial').forEach(function(boton) {

        boton.addEventListener('click', function() {

            const fila = boton.closest('tr');

            const textoCantidad = fila.querySelector('.cantidadTexto');
            const inputCantidad = fila.querySelector('.inputEditarCantidad');
            const btnGuardar = fila.querySelector('.btnGuardarEdicion');
            const btnCancelar = fila.querySelector('.btnCancelarEdicion');

            textoCantidad.classList.add('hidden');
            inputCantidad.classList.remove('hidden');

            boton.classList.add('hidden');
            btnGuardar.classList.remove('hidden');
            btnCancelar.classList.remove('hidden'); // ← Mostrar cancelar

            inputCantidad.focus();
        });

    });