
// Change main tabs
var changeTab = function(e, level = "") {
    var eid = $(e.target).parent().attr("id").split("_")[0];

    // TK: Add error checking

    // Get all elements with class="tablinks" and remove the class "active"
    $("." + level + "tablinks").each(function() {
      $(this).removeClass("active");
    });

    // hide all other tab content
    $("." + level + "tab-pane").each(function() {
      $(this).hide();
    });

    // Show the current tab, and add an "active" class to the button that opened the tab
    $('#' + eid + "_button").addClass("active");
    $('#' + eid + "_block").show();

    return false;
}

// For changing subtab menus
var changeSubTab = function(e) {
  changeTab(e, "sub");
  return false;
}

var removeCanonical = function(e) {
  $('.canonical').each(function() {
    $(this).remove();
    
    // hide the buttons
    $('div.canonical-event-metadata a').each(function() {
        $(this).hide();
    });
  });

  return false;
}

// MAIN -- document ready 
$(function(){ 
    // Show search block first
    $("#search_block").show();

    // Turn auto completes on
    $('.basicAutoComplete').autoComplete();

    // Add listener to tab links 
    $(".tablinks").each(function(){
        $(this).click(changeTab);
    });

    // Add listener to subtab links 
    $(".subtablinks").each(function(){
      $(this).click(changeSubTab);
    });

    // hide pane 1 + make other panes bigger
    $("#cand-events-hide").click(function() {
      $("#adj-pane-cand-events").hide();
      $("#cand-events-hide").hide();
      $("#cand-events-show").show();

      $("#adj-pane-expanded-view").removeClass("col-md-6");
      $("#adj-pane-expanded-view").addClass("col-md-12");
    
      $("#adj-pane-event-constructor").removeClass("col-md-6");
      $("#adj-pane-event-constructor").addClass("col-md-12");
    });

    // hide pane 1 + make other panes bigger
    $("#cand-events-show").click(function() {
      $("#cand-events-show").hide();
      $("#cand-events-hide").show();
      $("#adj-pane-cand-events").show();

      $("#adj-pane-expanded-view").removeClass("col-md-12");
      $("#adj-pane-expanded-view").addClass("col-md-6");

      $("#adj-pane-event-constructor").removeClass("col-md-12");
      $("#adj-pane-event-constructor").addClass("col-md-6");
    });

    //
    // Grid listeners
    // TK: Move these to somewhere else 
    // since the grid is created dynamically and won't be created on load
    //
    
    // Delete canonical event 
    $('div.canonical-event-metadata a.glyphicon-trash').click(function () {
      var r = confirm("Are you sure you want to delete the current canonical event?")
      if (r == false) {
        return;
      }

      // TK: remove from the database via Ajax call

      // if true, remove canonical event data from the DOM
      removeCanonical();
    });

    // Remove canonical event from grid
    $('div.canonical-event-metadata a.glyphicon-remove-sign').click(function () {
      var r = confirm("Are you sure you want to remove the canonical event from the grid?" +
        "\nThis DOES NOT delete the current canonical event.");

      if (r == false) {
        return;
      }
      
      removeCanonical();
    });

    // Modal listeners
    $('#new_canonical').click(function () {
      var url = $(this).data('url');
      $.get(url, function (data) {
        $('#modal-container .modal-content').html(data);
        $('#modal-container').modal('show');

        // form submission listener
        $('#modal-submit').click(function (event) {
          event.preventDefault();
          req = $.ajax({
            type: "POST",
            url: url.replace('view', 'add'),
            data: $('#modal-form').serialize()
          });
        
          req.done(function() {
            $("#modal-flash").text("Added successfully.");
            $("#modal-flash").removeClass("alert-danger");
            $("#modal-flash").addClass("alert-success");
            $("#modal-flash").show();

            // $('#modal-container').modal('hide');
            location.reload();
          });

          req.fail(function() {
            $("#modal-flash").text(req.responseText);
            $("#modal-flash").addClass("alert-danger");
            $("#modal-flash").show();
          });
        });
      })
    });
});