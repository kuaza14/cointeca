    document.addEventListener('DOMContentLoaded', function () {
        const tbody = document.getElementById('filasNuevosMateriales');
        const btnAgregar = document.getElementById('btnAgregarFilaMaterial');

        if (btnAgregar && tbody) {
            btnAgregar.addEventListener('click', function () {
                const primeraFila = tbody.querySelector('.fila-nuevo-material');
                if (primeraFila) {
                    const nuevaFila = primeraFila.cloneNode(true);
                    // Limpiar valores
                    const select = nuevaFila.querySelector('select[name="material_id[]"]');
                    if (select) select.selectedIndex = 0;
                    
                    const inputInst = nuevaFila.querySelector('input[name="cantidad_instalada[]"]') || nuevaFila.querySelector('input[name="cantidad[]"]');
                    if (inputInst) inputInst.value = '';
                    
                    const inputRet = nuevaFila.querySelector('input[name="cantidad_retirada[]"]');
                    if (inputRet) inputRet.value = '';

                    const aviso = nuevaFila.querySelector('.aviso-stock-container');
                    if (aviso) aviso.classList.add('hidden');

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
                        const sel = fila.querySelector('select[name="material_id[]"]');
                        if (sel) sel.selectedIndex = 0;
                        const inInst = fila.querySelector('input[name="cantidad_instalada[]"]') || fila.querySelector('input[name="cantidad[]"]');
                        if (inInst) inInst.value = '';
                        const inRet = fila.querySelector('input[name="cantidad_retirada[]"]');
                        if (inRet) inRet.value = '';
                        const aviso = fila.querySelector('.aviso-stock-container');
                        if (aviso) aviso.classList.add('hidden');
                    }
                }
            });

            // Al cambiar el material seleccionado, mostrar aviso si no hay stock
            tbody.addEventListener('change', function(e) {
                if (e.target && e.target.name === 'material_id[]') {
                    const select = e.target;
                    const selectedOption = select.options[select.selectedIndex];
                    const fila = select.closest('.fila-nuevo-material');
                    const aviso = fila ? fila.querySelector('.aviso-stock-container') : null;
                    const stockVal = selectedOption.getAttribute('data-stock');

                    if (aviso) {
                        if (select.value && (stockVal === null || parseFloat(stockVal) <= 0)) {
                            aviso.classList.remove('hidden');
                        } else {
                            aviso.classList.add('hidden');
                        }
                    }
                }
            });
        }

        // Edición inline en la tabla de materiales asociados
        document.querySelectorAll('.btnEditarMaterial').forEach(function(boton) {
            boton.addEventListener('click', function() {
                const fila = boton.closest('tr');

                const txtInst = fila.querySelector('.cantidadTextoInstalada') || fila.querySelector('.cantidadTexto');
                const inpInst = fila.querySelector('.inputEditarCantidadInstalada') || fila.querySelector('.inputEditarCantidad');
                
                const txtRet = fila.querySelector('.cantidadTextoRetirada');
                const inpRet = fila.querySelector('.inputEditarCantidadRetirada');

                const btnGuardar = fila.querySelector('.btnGuardarEdicion');
                const btnCancelar = fila.querySelector('.btnCancelarEdicion');

                if (txtInst) txtInst.classList.add('hidden');
                if (inpInst) inpInst.classList.remove('hidden');

                if (txtRet) txtRet.classList.add('hidden');
                if (inpRet) inpRet.classList.remove('hidden');

                boton.classList.add('hidden');
                if (btnGuardar) btnGuardar.classList.remove('hidden');
                if (btnCancelar) btnCancelar.classList.remove('hidden');

                if (inpInst) inpInst.focus();
            });
        });

        // Cancelar edición inline
        document.querySelectorAll('.btnCancelarEdicion').forEach(function(boton) {
            boton.addEventListener('click', function() {
                const fila = boton.closest('tr');

                const txtInst = fila.querySelector('.cantidadTextoInstalada') || fila.querySelector('.cantidadTexto');
                const inpInst = fila.querySelector('.inputEditarCantidadInstalada') || fila.querySelector('.inputEditarCantidad');
                
                const txtRet = fila.querySelector('.cantidadTextoRetirada');
                const inpRet = fila.querySelector('.inputEditarCantidadRetirada');

                const btnEditar = fila.querySelector('.btnEditarMaterial');
                const btnGuardar = fila.querySelector('.btnGuardarEdicion');

                if (txtInst) txtInst.classList.remove('hidden');
                if (inpInst) inpInst.classList.add('hidden');

                if (txtRet) txtRet.classList.remove('hidden');
                if (inpRet) inpRet.classList.add('hidden');

                if (btnEditar) btnEditar.classList.remove('hidden');
                if (btnGuardar) btnGuardar.classList.add('hidden');
                boton.classList.add('hidden');
            });
        });
    });