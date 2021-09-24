
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
 * @param {str} canonical_event_key - Desired canonical event record.
 * @param {str} cand_events_str - Desired candidate events.
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
  .fail(function() { return makeError(req.responseText); });
}

/**
 * Removes the block from the canonical record.
 * @returns true if successful, false otherwise.
 */
var removeCanonical = function () {
  var target = $(this).closest('.expanded-event-variable');
  var cel_id = target.attr('data-key');
  var variable = target.attr('data-var');
  var block_id = '#canonical-' + variable + '_' + cel_id;

  var req = $.ajax({
    type: 'POST',
    url: $SCRIPT_ROOT + '/del_canonical_record',
    data: {
      cel_id: cel_id
    }
  })
  .done(function() {
    // remove block
    $(block_id).remove();
    return true;
  })
  .fail(function() { return makeError(req.responseText); });
}

/**
 * Makes an success flash message.
 * @param {str} msg - Message to show. 
 */
 var makeSuccess = function(msg) {
  $('.flash').removeClass('alert-danger');
  $('.flash').addClass('alert-success');
  $('.flash').text(msg);
  $('.flash').show();
  $('.flash').fadeOut(5000);
  return true;
}

/**
 * Makes an error flash message.
 * @param {str} msg - Message to show. 
 */
var makeError = function(msg) {
  $('.flash').removeClass('alert-success');
  $('.flash').addClass('alert-danger');
  $('.flash').text(msg);
  $('.flash').show();
  $('.flash').fadeOut(5000);
  return false;
}

/**
 * Initialize listeners for grid buttons.
 * Need to perform this on load and on reload of grid.
 */
var initializeGridListeners = function() {
  /**
   * Additions
   */

  // Add a value to current canonical event
  $('.add-val').click(function(e) {
    var canonical_event_id = $('div.canonical-event-metadata').attr('id').split('_')[1];
    var variable = $(e.target).closest('.expanded-event-variable').attr('data-var').split('_')[0];

    // No canonical event, so error
    if (canonical_event_id == '') {
      makeError("Please select a canonical event first.");
      return false;
    }

    var req = $.ajax({
      type: 'POST',
      url: $SCRIPT_ROOT + '/add_canonical_record',
      data: {
        canonical_event_id: canonical_event_id,
        cec_id: $(e.target).attr('data-key')
      }
    })
    .done(function() {
      // remove the none block if it exists
      $('#canonical-event_' + variable + ' .none').remove();

      // make a block variable for the text and get ID
      var block = req.responseText;

      // add block to the canonical event variable
      $('#canonical-event_' + variable).append(block);

      // add remove listener by finding the last element 
      // added to this group of canonical cells
      var cells = $('#canonical-event_' + variable).children();
      $(cells[cells.length - 1]).find('a.remove-canonical').click(removeCanonical);
      return true;
    })
    .fail(function() { return makeError(req.responseText); });
  });

  // Link this event candidate event to the current canonical event
  $('.add-link').click(function(e) {
    var canonical_event_id = $('div.canonical-event-metadata').attr('id').split('_')[1];
    if (canonical_event_id == '') {
      makeError("Please select a canonical event first.");
      return false;
    }

    var column = $(e.target).closest('.candidate-event');
    var req = $.ajax({
      type: 'POST',
      url: $SCRIPT_ROOT + '/add_canonical_link',
      data: {
        canonical_event_id: canonical_event_id,
        event_id: column.attr('data-event'), 
        coder_name: column.attr('data-coder'), // TODO: Change the way we get the coder ID
        article_id: column.attr('data-article')
      }
    })
    .done(function() { 
      reloadGrid(
        canonical_event_key = $('div.canonical-event-metadata').attr('data-key'),
        cand_event_str = getCandidates()
      );
    })
    .fail(function() { return makeError(req.responseText); });
  });

  // Add flag for later review
  $('.add-flag').click(function(e) {


  });

  /**
   * Deletions and removals
   */

  // remove value from current canonical event
  $('.remove-canonical').click(removeCanonical);

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

  // Remove the link to this canonical event
  $('.remove-link').click(function (e) {
    var req = $.ajax({
      type: 'POST',
      url: $SCRIPT_ROOT + '/del_canonical_record',
      data: {
        cel_id: $(e.target).attr('data-key'),
        event_id: $(e.target).closest('.candidate-event').attr('data-event'),
        is_link: 1
      }
    })
    .done(function() {
      reloadGrid(
        canonical_event_key = $('div.canonical-event-metadata').attr('data-key'),
        cand_event_str = getCandidates()
      );
    })
    .fail(function() { return makeError(req.responseText); });    
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
      return makeSuccess(req.responseText);
    })
    .fail(function() { return makeError(req.responseText); });
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