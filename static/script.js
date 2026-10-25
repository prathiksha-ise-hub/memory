/* =====================================================
   DIGITAL MEMORY VAULT
   JAVASCRIPT
===================================================== */

document.addEventListener("DOMContentLoaded", function () {

    /* -----------------------------------------------
       SEARCH
    ------------------------------------------------ */

    const searchInput = document.getElementById("searchInput");

    if (searchInput) {

        searchInput.addEventListener("input", function () {

            const searchText =
                this.value.toLowerCase().trim();

            const cards =
                document.querySelectorAll(".file-card");

            cards.forEach(function (card) {

                const text =
                    card.innerText.toLowerCase();

                if (text.includes(searchText)) {

                    card.style.display = "flex";

                } else {

                    card.style.display = "none";

                }

            });

        });

    }


    /* -----------------------------------------------
       VAULT SEARCH
    ------------------------------------------------ */

    const vaultSearch =
        document.getElementById("vaultSearch");

    if (vaultSearch) {

        vaultSearch.addEventListener("input", function () {

            const searchText =
                this.value.toLowerCase().trim();

            const cards =
                document.querySelectorAll(".large-file-card");

            cards.forEach(function (card) {

                const text =
                    card.innerText.toLowerCase();

                if (text.includes(searchText)) {

                    card.style.display = "block";

                } else {

                    card.style.display = "none";

                }

            });

        });

    }


    /* -----------------------------------------------
       PASSWORD CONFIRMATION
    ------------------------------------------------ */

    const registerForm =
        document.querySelector(
            'form[action*="register"]'
        );

    if (registerForm) {

        registerForm.addEventListener(
            "submit",
            function (event) {

                const password =
                    document.querySelector(
                        'input[name="password"]'
                    );

                const confirmPassword =
                    document.querySelector(
                        'input[name="confirm_password"]'
                    );

                if (
                    confirmPassword &&
                    password.value !== confirmPassword.value
                ) {

                    event.preventDefault();

                    alert(
                        "Passwords do not match!"
                    );

                    confirmPassword.focus();

                }

            }
        );

    }


    /* -----------------------------------------------
       FILE INPUT
    ------------------------------------------------ */

    const fileInput =
        document.querySelector(
            'input[type="file"]'
        );

    if (fileInput) {

        fileInput.addEventListener(
            "change",
            function () {

                if (this.files.length > 0) {

                    const fileName =
                        this.files[0].name;

                    console.log(
                        "Selected file:",
                        fileName
                    );

                }

            }
        );

    }


    /* -----------------------------------------------
       FLASH MESSAGE AUTO HIDE
    ------------------------------------------------ */

    const alerts =
        document.querySelectorAll(".alert");

    alerts.forEach(function (alert) {

        setTimeout(function () {

            alert.style.transition =
                "opacity 0.5s ease";

            alert.style.opacity = "0";

            setTimeout(function () {

                alert.remove();

            }, 500);

        }, 4000);

    });


    /* -----------------------------------------------
       BUTTON CLICK EFFECT
    ------------------------------------------------ */

    const buttons =
        document.querySelectorAll(
            ".primary-btn"
        );

    buttons.forEach(function (button) {

        button.addEventListener(
            "click",
            function () {

                this.style.transform =
                    "scale(0.98)";

                setTimeout(() => {

                    this.style.transform = "";

                }, 120);

            }
        );

    });

});