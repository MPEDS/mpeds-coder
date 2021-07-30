
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

// MAIN -- document ready 
$(function(){ 
    $("#filters_block").show();

    // Add listener to tab links 
    $(".tablinks").each(function(){
        $(this).click(changeTab);
    });

    // Add listener to subtab links 
    $(".subtablinks").each(function(){
      $(this).click(changeSubTab);
    });

    // hide pane 1 + make other panes bigger
    $("#cand-events-hide").click(function(){
      $("#adj-pane-cand-events").hide();
      $("#cand-events-hide").hide();
      $("#cand-events-show").show();

      $("#adj-pane-expanded-view").removeClass("col-md-6");
      $("#adj-pane-expanded-view").addClass("col-md-12");
    
      $("#adj-pane-event-constructor").removeClass("col-md-6");
      $("#adj-pane-event-constructor").addClass("col-md-12");
    });

    // hide pane 1 + make other panes bigger
    $("#cand-events-show").click(function(){
      $("#cand-events-show").hide();
      $("#cand-events-hide").show();
      $("#adj-pane-cand-events").show();

      $("#adj-pane-expanded-view").removeClass("col-md-12");
      $("#adj-pane-expanded-view").addClass("col-md-6");

      $("#adj-pane-event-constructor").removeClass("col-md-12");
      $("#adj-pane-event-constructor").addClass("col-md-6");
    });
});