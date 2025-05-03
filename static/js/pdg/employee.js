
document.addEventListener("DOMContentLoaded", function () {

    new DataTable('#managers-table');
    new DataTable('#suppliers-table');
 
    const managersBtn = document.getElementById("managers-btn");
    const suppliersBtn = document.getElementById("suppliers-btn");
    const managerTable = document.getElementById("manager");
    const supplierTable = document.getElementById("supplier");

    // Function to update active header styles
    function updateActiveHeader(activeBtn, inactiveBtn) {
        activeBtn.style.color = "#FA4516";
        activeBtn.style.borderBottom = "2px solid #FA4516";
        activeBtn.style.fontWeight = "600";
        inactiveBtn.style.color = "#000";
        inactiveBtn.style.borderBottom = "none";
        inactiveBtn.style.fontWeight = "normal";
    }

    // Default view: managers
    managerTable.classList.remove("d-none");
    supplierTable.classList.add("d-none");
    updateActiveHeader(managersBtn, suppliersBtn);

    managersBtn.addEventListener("click", function () {
        managerTable.classList.remove("d-none");
        supplierTable.classList.add("d-none");
        updateActiveHeader(managersBtn, suppliersBtn);
    });

    suppliersBtn.addEventListener("click", function () {
        supplierTable.classList.remove("d-none");
        managerTable.classList.add("d-none");
        updateActiveHeader(suppliersBtn, managersBtn);
    });
});

