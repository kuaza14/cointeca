document.addEventListener("DOMContentLoaded", function () {

    const btnNuevoApoyo = document.getElementById("btnNuevoApoyo");
    const modalApoyo = document.getElementById("modalApoyo");

    if (btnNuevoApoyo && modalApoyo) {

        btnNuevoApoyo.addEventListener("click", function () {

            modalApoyo.classList.remove("hidden");
            modalApoyo.classList.add("flex");

        });
    }
});


function cerrarModalApoyo() {

    const modalApoyo = document.getElementById("modalApoyo");

    if (modalApoyo) {

        modalApoyo.classList.add("hidden");
        modalApoyo.classList.remove("flex");

    }

}