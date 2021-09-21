
/**
 * 
 * @param {*} e - Event
 * @param {*} level - Level of the tab (main, sub, etc.)
 * @returns false
 */
var changeTab = function(e, level = "") {
    var eid = $(e.target).parent().attr("id").split("_")[0];

    // TODO: Add error checking

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

/**
 * Wrapper to change subtabs 
 * @param {*} e - Event
 * @returns false
 * */ 
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

  // remove metadata ID
  $('.canonical-event-metadata').attr('id', null);
  return;
}

/**
 * Gets the current candidate events in the grid
 * @param {str} to_exclude - candidates to exclude
 * @return {str} - comma-separated string of candidate events
 */
var getCandidates = function(to_exclude = '') {
  // get the current candidate events, minus the one that was clicked
  var candidate_event_ids = []; 
  var cand_events = document.getElementsByClassName('candidate-event');
  for (var i = 0; i < cand_events.length; i++) {
    var id = $(cand_events[i]).attr('id').split('_')[1];
    if (id != to_exclude) {
      candidate_event_ids.push(id);
    }
  }
  return candidate_event_ids.join()
}

/**
 * Reloads the grid for adding and removing candidate and canonical events.
 * @param {string} canonical_event_key - Desired canonical event record.
 * @param {string} cand_events_str - Desired candidate events.
 * @returns false on failure, true on success
 */
var reloadGrid = function(canonical_event_key = null, cand_events_str = null) {
  // reload grid
  var req = $.ajax({
    type: "GET",
    url:  $SCRIPT_ROOT + '/load_adj_grid',
    data: {
      canonical_event_key: canonical_event_key,
      cand_events: cand_events_str
    },
    beforeSend: function () {
      $('.flash').addClass('alert-info');
      $('.flash').text("Loading...");
      $('.flash').show();
      }
  })
  .done(function() {
    // add HTML to grid
    $('#adj-grid').html(req.responseText);

    // reset URL params
    let search_params = new URLSearchParams(window.location.search);
    search_params.delete('canonical_event_key');
    search_params.append('canonical_event_key', canonical_event_key);
    
    search_params.delete('cand_events');
    search_params.append('cand_events', cand_events_str);
    
    var new_url = 'adj?' + search_params.toString();
    window.history.pushState({path: new_url}, '', new_url);

    // reinitiatize grid listeners
    initializeGridListeners();

    // get rid of loading flash 
    $('.flash').hide();
    $('.flash').removeClass('alert-info');
    return true;
  })
  .fail(function() {
    $('.flash').text(req.responseText);
    $('.flash').removeClass('alert-success');
    $('.flash').addClass('alert-danger');
    $('.flash').show();
    
    return false;
  });
}

/**
 * Initialize listeners for grid buttons.
 * Need to perform this on load and on reload of grid.
 */
var initializeGridListeners = function() {
  
  /**
   * Additions
   */

  // add a value to current canonical event
  $('.add-val').each(function() {
    $(this).click(function() {
      var canonical_event_id = $('div.canonical-event-metadata').attr('id').split('_')[1];
      var variable = $(this).closest('.expanded-event-variable').attr('data-var').split('_')[0];

      // No canonical event, so error
      if (canonical_event_id == '') {
        $('.flash').addClass('alert-danger');
        $('.flash').text("Please select a canonical event first.");
        $('.flash').show();
        $('.flash').fadeOut(5000);
        return;
      }

      var req = $.ajax({
        type: 'POST',
        url: $SCRIPT_ROOT + '/add_canonical_record',
        data: {
          canonical_event_id: canonical_event_id,
          cec_id: $(this).attr('data-key'),
          is_link: 0
        }
      })
      .done(function() {
        // remove the none block if it exists
        $('#canonical-event_' + variable + ' .none').remove();

        // add block to the canonical event variable
        $('#canonical-event_' + variable).append(req.responseText);

        // TODO: Re-add delete button listener
      })
      .fail(function() {
        // error
        $('.flash').addClass('alert-danger');
        $('.flash').text(req.responseText);
        $('.flash').show();
        $('.flash').fadeOut(5000);
      });
    }); 
  });

  /**
   * Deletions and removals
   */

  // remove value from current canonical event
  $('.remove-canonical').click(function (e) {
    var cel_id = $(this).closest('.expanded-event-variable').attr('data-key');

    var req = $.ajax({
      type: 'POST',
      url: $SCRIPT_ROOT + '/del_canonical_record',
      data: {
        cel_id: cel_id,
        is_link: 0
      }
    })
    .done(function() {
      // remove block
      // TODO: This doesn't work! why not?
      console.log($(e.current_target));
      console.log($(this).closest('.expanded-event-variable'));

      // TODO: add (none) block, if necessary
    })
    .fail(function() {
      // error
      $('.flash').addClass('alert-danger');
      $('.flash').text(req.responseText);
      $('.flash').show();
      $('.flash').fadeOut(5000);
    });
  });

  // Remove candidate event from grid
  $('.remove-candidate').click(function() {
      // get current canonical key, if it exists
      var canonical_event_key = $('div.canonical-event-metadata');
      if (canonical_event_key) {
        canonical_event_key = canonical_event_key.attr('data-key');
      }

      // the current event to exclude
      var cand_metadata = $(this).closest('.candidate-event');
      var to_exclude = cand_metadata.attr('id').split('_')[1];
      
      reloadGrid(
          canonical_event_key = canonical_event_key, 
          cand_event_str = getCandidates(to_exclude)
      );
  });

  // Delete canonical event 
  $('div.canonical-event-metadata a.glyphicon-trash').click(function () {
    var r = confirm("Are you sure you want to delete the current canonical event?")
    if (r == false) {
      return;
    }

    var canonical_event_id = $('div.canonical-event-metadata').attr('id').split('_')[1];

    // remove from the database via Ajax call
    var req = $.ajax({
      url: $SCRIPT_ROOT + '/_del_canonical_event',
      type: "POST",
      data: {
        id: canonical_event_id
      }
    })
    .done(function() {
      reloadGrid('', getCandidates());

      $('.flash').text(req.responseText);
      $('.flash').removeClass('alert-danger');
      $('.flash').addClass('alert-success');
      $('.flash').show()

      $('.flash').fadeOut(3000);
    })
    .fail(function() { 
      $('.flash').text(req.responseText);
      $('.flash').removeClass('alert-success');
      $('.flash').addClass('alert-danger');
      $('.flash').show();
    });
  });

  // Remove canonical event from grid
  $('div.canonical-event-metadata a.glyphicon-remove-sign').click(function () {
    var canonical_event_id = $('div.canonical-event-metadata').attr('id').split('_')[1];
    var success = reloadGrid('', getCandidates());

    // Change the buttons in the search section
    if (success) {
      $('#search-canonical-event_' + canonical_event_id + ' b.ce-isactive').hide();
      $('#search-canonical-event_' + canonical_event_id + ' b.ce-makeactive').show();
    }
  });
}

// MAIN -- document ready 
$(function(){ 
    // Show search block first
    $("#search_block").show();

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
          })
          .done(function() {
            $("#modal-flash").text("Added successfully.");
            $("#modal-flash").removeClass("alert-danger");
            $("#modal-flash").addClass("alert-success");
            $("#modal-flash").show();

            // $('#modal-container').modal('hide');
            location.reload();
          })
          .fail(function() {
            $("#modal-flash").text(req.responseText);
            $("#modal-flash").addClass("alert-danger");
            $("#modal-flash").show();
          });
        });
      })
    });

    // ********************************
    // Search box listeners
    // TODO: Move these to somewhere else
    // since the searches are created dynamically
    // ********************************

    // listeners to make the current canonical ID active
    $('b.ce-makeactive').each(function () {
      $(this).click(function () {
        // get key and id from event-desc
        var search_canonical_event = $(this).closest('.event-desc');
        var canonical_event_id  = search_canonical_event.attr('id').split('_')[1];
        var canonical_event_key = search_canonical_event.attr('data-key');
        
        var success = reloadGrid(
          canonical_event_key = canonical_event_key, 
          cand_events_str = getCandidates()
        );

        if (success) {
          // toggle search buttons
          $('#search-canonical-event_' + canonical_event_id + ' b.ce-isactive').show();
          $('#search-canonical-event_' + canonical_event_id + ' b.ce-makeactive').hide();
        }
      });
    });

    initializeGridListeners();
});