 // Activer le menu burger
 document.querySelectorAll('.nav-link').forEach(link => {
    link.addEventListener('click', () => {
      const navbarCollapse = document.querySelector('.navbar-collapse');
      if (navbarCollapse.classList.contains('show')) {
        navbarCollapse.classList.remove('show');
      }
    });
  });

  // Animation de l'image de l'application
  window.addEventListener('scroll', function() {
      const appImage = document.getElementById('appImage');
      const appImagePosition = appImage.getBoundingClientRect().top;
      const screenPosition = window.innerHeight / 1.3;
      
      if(appImagePosition < screenPosition) {
          appImage.classList.add('animate');
      }
  });