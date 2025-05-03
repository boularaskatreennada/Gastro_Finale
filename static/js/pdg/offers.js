document.addEventListener("DOMContentLoaded", function () {
    // Récupérer les boutons et les tableaux
    const buttons = {
        all: document.getElementById("All-btn"),
        active: document.getElementById("active-btn"),
        upcoming: document.getElementById("upcoming-btn"),
        expired: document.getElementById("expired-btn"),
    };

    const tables = {
        all: document.getElementById("All"),
        active: document.getElementById("Active"),
        upcoming: document.getElementById("upcoming"),
        expired: document.getElementById("expired"),
    };

    function styleSelectedButton(selectedKey) {
        Object.keys(buttons).forEach((key) => {
            const btn = buttons[key];
            btn.style.position = "relative";
            btn.style.paddingBottom = "10px"; // spacing for the red underline
            if (key === selectedKey) {
                btn.style.color = "#FA4516";
                btn.style.fontWeight = "600";
                btn.style.borderBottom = "none";

                // Add red underline as a pseudo-line over gray
                btn.style.boxShadow = "inset 0 -2px 0 0 #FA4516";
            } else {
                btn.style.color = "#333";
                btn.style.fontWeight = "normal";
                btn.style.boxShadow = "none";
            }
        });
    }

    function showTable(selected) {
        Object.keys(tables).forEach((key) => {
            tables[key].style.display = key === selected ? "block" : "none";
        });

        styleSelectedButton(selected);
    }

    showTable("all");

    new DataTable('#All-table');
    new DataTable('#active-table');
    new DataTable('#upcoming-table');
    new DataTable('#expired-table');
    
    buttons.all.addEventListener("click", () => showTable("all"));
    buttons.active.addEventListener("click", () => showTable("active"));
    buttons.upcoming.addEventListener("click", () => showTable("upcoming"));
    buttons.expired.addEventListener("click", () => showTable("expired"));

    // Afficher par défaut "All"
    showTable("all");
});
