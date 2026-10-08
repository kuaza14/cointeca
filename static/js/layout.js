/**
 * COINTECA S.A.S. - Sistema de Gestión Empresarial
 * layout.js - Control global de la interfaz, barra lateral, paneles flotantes y prevención de doble envío.
 */

(function () {
    'use strict';

    // =========================================================================
    // BARRA LATERAL (SIDEBAR) RESPONSIVA Y DROPDOWNS
    // =========================================================================
    const barra = document.getElementById("barraLateral");
    const fondo = document.getElementById("fondoBarraLateral");
    const btnMenu = document.getElementById("btnMenu");
    const btnAlertas = document.getElementById("btnAlertas");
    const panelAlertas = document.getElementById("panelAlertas");
    const btnUsuario = document.getElementById("btnUsuario");
    const menuUsuario = document.getElementById("menuUsuario");

    function abrirMenu() {
        if (barra) barra.classList.add("menu-abierto");
        if (fondo) fondo.classList.remove("hidden");
        if (btnMenu) btnMenu.setAttribute("aria-expanded", "true");
    }

    function cerrarMenu() {
        if (barra) barra.classList.remove("menu-abierto");
        if (fondo) fondo.classList.add("hidden");
        if (btnMenu) btnMenu.setAttribute("aria-expanded", "false");
    }

    if (btnMenu) {
        btnMenu.addEventListener("click", function () {
            const abierto = barra && barra.classList.contains("menu-abierto");
            if (abierto) {
                cerrarMenu();
            } else {
                abrirMenu();
            }
        });
    }

    if (fondo) {
        fondo.addEventListener("click", cerrarMenu);
    }

    // Panel de alertas (Notificaciones)
    if (btnAlertas && panelAlertas) {
        btnAlertas.addEventListener("click", function (e) {
            e.stopPropagation();
            panelAlertas.classList.toggle("hidden");
            if (menuUsuario) menuUsuario.classList.add("hidden");
        });
    }

    // Menú desplegable de usuario
    if (btnUsuario && menuUsuario) {
        btnUsuario.addEventListener("click", function (e) {
            e.stopPropagation();
            menuUsuario.classList.toggle("hidden");
            if (panelAlertas) panelAlertas.classList.add("hidden");
        });
    }

    // Cerrar dropdowns al hacer clic fuera
    document.addEventListener("click", function () {
        if (panelAlertas) panelAlertas.classList.add("hidden");
        if (menuUsuario) menuUsuario.classList.add("hidden");
    });

    // =========================================================================
    // PREVENCIÓN GLOBAL DE DOBLE ENVÍO EN FORMULARIOS (DOUBLE-SUBMIT GUARD)
    // =========================================================================
    document.addEventListener("submit", function (e) {
        const form = e.target;
        if (!form || (form.method && form.method.toUpperCase() === "GET")) return;
        if (e.defaultPrevented) return;

        // Si el formulario ya está en proceso de envío, bloquear segundo clic
        if (form.dataset.submitting === "true") {
            e.preventDefault();
            e.stopImmediatePropagation();
            return false;
        }

        form.dataset.submitting = "true";

        const submitBtns = form.querySelectorAll('button[type="submit"], input[type="submit"]');
        submitBtns.forEach(function (btn) {
            btn.style.pointerEvents = "none";
            setTimeout(function () {
                btn.disabled = true;
                btn.classList.add("opacity-70", "cursor-not-allowed");
                if (btn.tagName === "BUTTON" && !btn.querySelector(".spinner-anti-double")) {
                    const spinner = document.createElement("span");
                    spinner.className = "spinner-anti-double mr-1.5 inline-block animate-spin";
                    spinner.innerHTML = "⏳";
                    btn.prepend(spinner);
                }
            }, 20);
        });
    }, false);

    window.addEventListener("pageshow", function () {
        document.querySelectorAll('form[data-submitting="true"]').forEach(function (form) {
            delete form.dataset.submitting;
            form.querySelectorAll('button[type="submit"], input[type="submit"]').forEach(function (btn) {
                btn.disabled = false;
                btn.style.pointerEvents = "";
                btn.classList.remove("opacity-70", "cursor-not-allowed");
                const sp = btn.querySelector(".spinner-anti-double");
                if (sp) sp.remove();
            });
        });
    });
})();
