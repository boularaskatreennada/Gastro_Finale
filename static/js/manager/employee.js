document.addEventListener("DOMContentLoaded", function () {
    
    new DataTable('#servers-table');
    new DataTable('#chefs-table');
    new DataTable('#delivery-table');
    


    const serversBtn = document.getElementById("servers-btn");
    const chefsBtn = document.getElementById("chefs-btn");
    const deliveryBtn = document.getElementById("delivery-btn");

    const serverTable = document.getElementById("server");
    const chefTable = document.getElementById("chef");
    const deliveryTable = document.getElementById("delivery");

    const buttons = [serversBtn, chefsBtn, deliveryBtn];

    // Function to hide all tables
    function hideAllTables() {
        serverTable.classList.add("d-none");
        chefTable.classList.add("d-none");
        deliveryTable.classList.add("d-none");
    }

    serverTable.classList.remove("d-none");
        serversBtn.style.color = "#FA4516";
        serversBtn.style.borderBottom = "2px solid #FA4516";
    // Function to reset button styles
    function resetButtonStyles() {
        buttons.forEach(button => {
            button.style.color = ""; 
            button.style.borderBottom = "";
        });
    }

    // Event listeners for buttons
    serversBtn.addEventListener("click", function () {
        hideAllTables();
        resetButtonStyles();
        serverTable.classList.remove("d-none");
        serversBtn.style.color = "#FA4516";
        serversBtn.style.borderBottom = "2px solid #FA4516";
    });

    chefsBtn.addEventListener("click", function () {
        hideAllTables();
        resetButtonStyles();
        chefTable.classList.remove("d-none");
        chefsBtn.style.color = "#FA4516";
        chefsBtn.style.borderBottom = "2px solid #FA4516";
    });

    deliveryBtn.addEventListener("click", function () {
        hideAllTables();
        resetButtonStyles();
        deliveryTable.classList.remove("d-none");
        deliveryBtn.style.color = "#FA4516";
        deliveryBtn.style.borderBottom = "2px solid #FA4516";
    });
});