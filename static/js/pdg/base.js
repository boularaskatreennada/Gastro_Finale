const toggleBtn = document.querySelector(".toggle-btn");
const toggler =document.querySelector("#icon");

toggleBtn.addEventListener("click",function(){
    document.querySelector("#sidebar").classList.toggle("expand");
    
    if (toggler.classList.contains('bxs-chevrons-right')) {
        toggler.classList.remove('bxs-chevrons-right');
        toggler.classList.add('bxs-chevrons-left');
    } else {
        toggler.classList.remove('bxs-chevrons-left');
        toggler.classList.add('bxs-chevrons-right');
    }
})