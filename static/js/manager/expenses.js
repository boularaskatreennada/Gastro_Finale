document.addEventListener('DOMContentLoaded', function () {
    
    $('#complaints-table').DataTable();
    $('#expense-search').on('keyup', function () {
      table.search(this.value).draw();
    });


    
  $(document).ready(function() {
      const table = $('#expenses-table').DataTable();
      $('#orders-table').DataTable();
      $('#complaints-table').DataTable();

      $('#show-orders').on('click', function() {
          $('#orders-section').removeClass('d-none');
          $('#complaints-section').addClass('d-none');
          $(this).addClass('active');
          $('#show-complaints').removeClass('active');
      });

      $('#show-complaints').on('click', function() {
          $('#complaints-section').removeClass('d-none');
          $('#orders-section').addClass('d-none');
          $(this).addClass('active');
          $('#show-orders').removeClass('active');
      });
  });

  });