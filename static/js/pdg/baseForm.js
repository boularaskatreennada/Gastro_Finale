document.getElementById('id_photo').addEventListener('change', function () {
  const file = this.files[0];
  const preview = document.getElementById('previewImage');
  const icon = document.getElementById('uploadIcon');

  if (file) {
      const reader = new FileReader();
      reader.onload = function (e) {
          preview.src = e.target.result;
          preview.style.display = 'block';
          if (icon) icon.style.display = 'none';
      };
      reader.readAsDataURL(file);
  }
});


function collectIngredients() {
    const items = document.querySelectorAll('.ingredient-item');
    const result = [];

    items.forEach(item => {
      const checkbox = item.querySelector('.ingredient-checkbox');
      if (checkbox.checked) {
        result.push({
          name: checkbox.value,
          quantity: item.querySelector('.ingredient-qty').value,
          unit: item.querySelector('.ingredient-unit').value
        });
      }
    });

    document.getElementById('ingredients_data').value = JSON.stringify(result);
  }

  document.querySelector('form').addEventListener('submit', function (e) {
    collectIngredients();
  });



