
/**
 * 
 * @param {*} e - Event
 * @param {*} level - Level of the tab (main, sub, etc.)
 * @returns false
 */
var changeTab = function(e, level = "") {
    var label = $(e.target).parent().attr("id").split("_")[0];

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
    $('#' + label + "_button").addClass("active");
    $('#' + label + "_block").show();

    // if this has a *, remove
    var button_text = $('#' + label + '_button-link').text();
    if (button_text.indexOf("*") > -1) {
      button_text = button_text.replace("*", "");
      $('#' + label + '_button-link').html(button_text);
    }

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
 * Loads the grid for adding and removing candidate and canonical events.
 * @param {str} canonical_event_key - Desired canonical event record.
 * @param {str} cand_events_str - Desired candidate events.
 * @returns false on failure, true on success
 */
var loadGrid = function(canonical_event_key = null, cand_events_str = null) {
  var req = $.ajax({
    type: "GET",
    url:  $SCRIPT_ROOT + '/load_adj_grid',
    data: {
      canonical_event_key: canonical_event_key,
      cand_events: cand_events_str
    },
    beforeSend: function () {
      $('.flash').removeClass('alert-danger');
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

  return true;
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
 * Loads the search results for the given query from the existing forms.
 * @returns true if successful, false otherwise.
 */
 var loadSearch = function() {
  var req = $.ajax({
    url: $SCRIPT_ROOT + '/do_search',
    type: "POST",
    data: 
      $('#adj_search_form, #adj_filter_form, #adj_sort_form').serialize(),
    beforeSend: function () {
      $('.flash').removeClass('alert-danger');
      $('.flash').addClass('alert-info');
      $('.flash').text("Loading...");
      $('.flash').show();
    }
  })
  .done(function() {
    // Update content block.
    $('#cand-search_block').html(req.responseText); 

    // Update the search button text.
    n_results = req.getResponseHeader('Search-Results');
    $('#cand-search-text').text("Search (" + n_results + " results)");

    // Update the candidate button text.
    $('#cand_button-link').text("Candidate Events*");

    // Update the URL search params.
    let curr_search_params = new URLSearchParams(window.location.search);
    var search_params = jQuery.parseJSON(req.getResponseHeader('Query'));
    for (var key in search_params) {
      curr_search_params.set(key, search_params[key]);
    }

    var new_url = 'adj?' + curr_search_params.toString();
    window.history.pushState({path: new_url}, '', new_url);

    markGridEvents();
    initializeSearchListeners();

    // get rid of loading flash 
    $('.flash').hide();
    $('.flash').removeClass('alert-info');
    return true;
  })
  .fail(function() { return makeError(req.responseText); });
}


/**
 * Toggles flags for candidate events.
 * @param {Event} e - click event
 * @param {str} operation - add or deletion operation. takes values 'add' or 'del'
 * @param {str} flag - the flag to add to this event
 * @returns true if successful, false otherwise.
 */
var toggleFlag = function(e, operation, flag) {
  if (operation != 'add' & operation != 'del') {
    return false;
  }

  var column = $(e.target).closest('.candidate-event');
  var req = $.ajax({
    type: 'POST',
    url: $SCRIPT_ROOT + '/' + operation + '_event_flag',
    data: {
      event_id: column.attr('data-event'), 
      flag: flag
    }
  })
  .done(function() { 
    // remove this event if we're adding a completed flag
    to_exclude = '';
    if (operation == 'add' & flag == 'completed') {
      to_exclude = column.attr('data-event');
    }

    return loadGrid(
      canonical_event_key = $('div.canonical-event-metadata').attr('data-key'),
      cand_event_str = getCandidates(to_exclude)
    );
  })
  .fail(function() { return makeError(req.responseText); });
}


/**
 * 
 * @param {str} mode - add or edit 
 */
var updateModal = function (variable, mode) {
  var req = $.ajax({
    type: "POST",
    url: $SCRIPT_ROOT + '/modal_edit/' + variable + '/' + mode,
    data: $('#modal-form').serialize()
  })
  .done(function() {
    $("#modal-flash").text("Added successfully.");
    $("#modal-flash").removeClass("alert-danger");
    $("#modal-flash").addClass("alert-success");
    $("#modal-flash").show();
    $('#modal-container').modal('hide');

    // update the grid with new canonical event if it exists
    var reload_key = null;
    if($("#canonical-event-key").val() !== undefined) {
      reload_key = $("#canonical-event-key").val();
    } else {
      // otherwise, reload the current grid
      reload_key = $('.canonical-event-metadata').attr('data-key');
    }

    loadGrid(
      canonical_event_key = reload_key,
      cand_events_str = getCandidates()
    );
  })
  .fail(function() {
    $("#modal-flash").text(req.responseText);
    $("#modal-flash").addClass("alert-danger");
    $("#modal-flash").show();
  });
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
 * Marks the given candidate events as in the grid.
 * @param {str} cand_events - optional array of candidate event ids.
 *  */
var markGridEvents = function(cand_events = null) {
  // If we don't get cand_events, get them from the URL.
  if(cand_events == null) {
    var search_params = new URLSearchParams(window.location.search);
    cand_events = search_params.get('cand_events').split(',');
  }

  // Mark all events as not in the grid.
  $('.event-desc.candidate-search').each(function() {
    $(this).find('.cand-isactive').hide();
    $(this).find('.cand-makeactive').show();
  });

  // Mark events which are in the grid as active.
  for (var i = 0; i < cand_events.length; i++) {
    let event_desc = $('.event-desc[data-event="' + cand_events[i] + '"]');
    event_desc.find('.cand-isactive').show();
    event_desc.find('.cand-makeactive').hide();
  }
}

/**
 * Marks the given canonical event as in the grid.
 * @param {str} event_desc - optional element to mark as active.
 */
var markCanonicalGridEvent = function(event_desc = null) {
  // Mark all canonical event search results as not in the grid.
  $('.event-desc.canonical-search').each(function() {
    $(this).find('.canonical-isactive').hide();
    $(this).find('.canonical-makeactive').show();
  });

  // Mark the current canonical event as active.
  if (event_desc != null) {
    event_desc.find('.canonical-isactive').show();
    event_desc.find('.canonical-makeactive').hide();
  }
};

/**
 * 
 * @param {*} e - event
 * @param {*} variable - variable to be expanded
 */
var expandDesc = function(e, variable) {
  $('.expanded-event-variable[data-var=' + variable + ']').each(function() {
    $(this).addClass('maximize');
  });

  $('#expand-' + variable).hide();
  $('#collapse-' + variable).show();
}

/**
 * 
 * @param {*} e - event 
 * @param {*} variable - variable to be collapse
 */
var collapseDesc = function(e, variable) {
  $('.expanded-event-variable[data-var=' + variable + ']').each(function() {
    $(this).removeClass('maximize');
  });

  $('#expand-' + variable).show();
  $('#collapse-' + variable).hide();
}

/**
 * Initialize listeners for search pane.
 * Will need to perform this on every reload of the search pane.
 * 
 */
var initializeSearchListeners = function() {
  var MAX_CAND_EVENTS = 4;

  // listeners for current search results
  $('.cand-makeactive').click(function(e) {
    e.preventDefault();

    var search_params = new URLSearchParams(window.location.search);

    var event_desc = $(e.target).closest('.event-desc');
    var event_id = event_desc.attr('data-event');
    var cand_events = search_params.get('cand_events').split(',');  

    // remove last event from the list if full
    if (cand_events.length == MAX_CAND_EVENTS) {
      cand_events.pop();
    } else if (cand_events.length == 1 & (cand_events[0] == 'null' | cand_events[0] == '')) {
      // remove the null keyword
      cand_events = [];
    }

    // add this event to the list
    cand_events.push(event_id);

    let success = loadGrid(
      canonical_event_key = search_params.get('canonical_event_key'),
      cand_events_str = cand_events.join(',')
    );

    if (success) {
      markGridEvents(cand_events);
    }

    return true;
  });
}

/**
 * Initialize canonical search listeners.
 */
var initializeCanonicalSearchListeners = function() {
  // Listener for canonical event search.
  $('.canonical-makeactive').click(function (e) {
    e.preventDefault();

    // get event desc
    var event_desc = $(e.target).closest('.event-desc');

    // get key and id from event-desc
    var canonical_event_key = event_desc.attr('data-key');
    
    var success = loadGrid(
      canonical_event_key = canonical_event_key, 
      cand_events_str = getCandidates()
    );

    if (success) {
      markCanonicalGridEvent(event_desc);
    }
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
        article_id: column.attr('data-article')
      }
    })
    .done(function() { 
      loadGrid(
        canonical_event_key = $('div.canonical-event-metadata').attr('data-key'),
        cand_event_str = getCandidates()
      );
    })
    .fail(function() { return makeError(req.responseText); });
  });

  // add completed flag to candidate event
  $('.add-completed').click(function(e) { toggleFlag(e, 'add', 'completed'); });

  // add further review flag to candidate event
  $('.add-flag').click(function(e) { toggleFlag(e, 'add', 'for-review');  });

  // add value to a new dummy event
  $('.add-dummy').click(function(e) {
    var variable = $(e.target).closest('.expanded-event-variable-name').attr('data-var');
    var canonical_event_key = $('.canonical-event-metadata').attr('data-key');

    if(canonical_event_key == '') {
      makeError("Please select a canonical event first.");
      return false;
    }

    var req = $.ajax({
      type: 'POST',
      url: $SCRIPT_ROOT + '/modal_view',
      data: {
        candidate_event_ids: getCandidates(),
        variable: variable,
        key: canonical_event_key
      }
    })
    .done(function() {
      $('#modal-container .modal-content').html(req.responseText);
      $('#modal-container').modal('show');

      // add date pickers
      $('#modal-container .date').datetimepicker({ format: 'YYYY-MM-DD' });        

      $('#modal-submit').click(function(e) {
        e.preventDefault(); 
        updateModal(variable, 'add');
      });

    })
    .fail(function() { return makeError("Could not load modal."); })
  });

  // Select all text in the current candidate event box.
  $('.select-text').click(function(e) {
    e.preventDefault();

    var text = $(e.target).closest('.expanded-event-variable');
    let range = document.createRange();
    range.selectNodeContents(text[0]);
    window.getSelection().addRange(range);
  });

  // edit a canonical event metadata
  $('.edit-canonical').click(function(e) {
    var canonical_event_key = $(e.target).closest('.canonical-event-metadata').attr('data-key');
    var req = $.ajax({
      type: 'POST',
      url: $SCRIPT_ROOT + '/modal_view',
      data: {
        variable: 'canonical',
        key: canonical_event_key
      }
    })
    .done(function() {
      $('#modal-container .modal-content').html(req.responseText);
      $('#modal-container').modal('show');

      $('#modal-submit').click(function(e) { 
        e.preventDefault(); 
        updateModal('canonical', 'edit'); 
      });      
    })
    .fail(function() { return makeError("Could not load modal."); })
  });

  // Toggle metadata visibility.
  $('#hide-metadata').click(function(e) {
    $('.expanded-event-variable-metadata').hide();
    $('.canonical-event-metadata .expanded-event-variable').hide();
    $('#show-metadata').show();
    $('#hide-metadata').hide();
  });

  $('#show-metadata').click(function(e) {
    $('.expanded-event-variable-metadata').show();
    $('.canonical-event-metadata .expanded-event-variable').show();
    $('#show-metadata').hide();
    $('#hide-metadata').show();
  });

  // Toggle the expansion of the article-desc and the desc.
  $('#expand-article-desc').click(function(e) { expandDesc(e, 'article-desc') }); 
  $('#expand-desc').click(function(e) { expandDesc(e, 'desc') }); 
  $('#collapse-article-desc').click(function(e) { collapseDesc(e, 'article-desc') });
  $('#collapse-desc').click(function(e) { collapseDesc(e, 'desc') });

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
      
      loadGrid(
          canonical_event_key = canonical_event_key, 
          cand_event_str = getCandidates(to_exclude)
      );

      markGridEvents();
  });

  // Remove the link to this canonical event
  $('.remove-link').click(function (e) {
    var req = $.ajax({
      type: 'POST',
      url: $SCRIPT_ROOT + '/del_canonical_link',
      data: {
        article_id: $(e.target).attr('data-article')
      }
    })
    .done(function() {
      loadGrid(
        canonical_event_key = $('div.canonical-event-metadata').attr('data-key'),
        cand_event_str = getCandidates()
      );
    })
    .fail(function() { return makeError(req.responseText); });    
  });

  // Remove completed
  $('.remove-completed').click(function(e) { toggleFlag(e, 'del', 'completed') });

  // Remove flag
  $('.remove-flag').click(function(e) { toggleFlag(e, 'del', 'for-review') });

  // Delete canonical event 
  $('div.canonical-event-metadata a.glyphicon-trash').click(function () {
    var r = confirm("Are you sure you want to delete the current canonical event?")
    if (r == false) {
      return;
    }

    var canonical_event_id = $('div.canonical-event-metadata').attr('id').split('_')[1];

    // remove from the database via Ajax call
    var req = $.ajax({
      url: $SCRIPT_ROOT + '/del_canonical_event',
      type: "POST",
      data: {
        id: canonical_event_id
      }
    })
    .done(function() {
      loadGrid('', getCandidates());
      return makeSuccess(req.responseText);
    })
    .fail(function() { return makeError(req.responseText); });
  });

  // Remove canonical event from grid
  $('div.canonical-event-metadata a.glyphicon-remove-sign').click(function () {
    var success = loadGrid('', getCandidates());

    // Change the buttons in the search section
    if (success) {
      markCanonicalGridEvent();
    }
  });
}

// MAIN -- document ready 
$(function () { 
    // Show search block first
    $("#search_block").show();

    // Add listener to tab links 
    $(".tablinks").each(function(){
        $(this).click(changeTab);
    });

    // Add listener to subtab links 
    $(".cand-subtablinks").each(function(){
      $(this).click(function(e) { changeTab(e, 'cand-sub'); });
    });

    $(".canonical-subtablinks").each(function(){
      $(this).click(function(e) { changeTab(e, 'canonical-sub'); });
    });

    // hide search panel
    $("#cand-events-hide").click(function() {
      $("#adj-pane-cand-events").hide();
      $("#cand-events-hide").hide();
      $("#cand-events-show").show();

      $("#adj-pane-expanded-view").removeClass("col-md-7");
      $("#adj-pane-expanded-view").addClass("col-md-12");
    });

    // show search pane
    $("#cand-events-show").click(function() {
      $("#cand-events-show").hide();
      $("#cand-events-hide").show();
      $("#adj-pane-cand-events").show();

      $("#adj-pane-expanded-view").removeClass("col-md-12");
      $("#adj-pane-expanded-view").addClass("col-md-7");
    });

    // Listener to create a new canonical event
    $('#new-canonical').click(function () {;
      var req = $.ajax({
        url: $SCRIPT_ROOT + '/modal_view', 
        type: "POST",
        data: {
          variable: 'canonical'
        }
      })
      .done(function() {
        $('#modal-container .modal-content').html(req.responseText);
        $('#modal-container').modal('show');
        $('#modal-submit').click(function(e) {
          e.preventDefault(); 
          updateModal('canonical', 'add');
        });
      })
    });

    // Listener for search button.
    $('#adj_search_button').click(loadSearch);

    // Listener for clear button.
    $('.clear-values').each(function() {
      $(this).click(function() {
        // Clear the search form and clear URL parameters
        let search_params = new URLSearchParams(window.location.search);

        $(this).closest('.form-row').find('input').each(function() {
          $(this).val('');
          search_params.set($(this).attr('name'), '');
        });
        $(this).closest('.form-row').find('select').each(function() {
          $(this).val('');
          search_params.set($(this).attr('name'), '');
        });

        // Update the URL with cleared values
        var new_url = 'adj?' + search_params.toString();
        window.history.pushState({path: new_url}, '', new_url);    
      });
    });

    // Listener for canonical event search
    $('#canonical-search-button').click(function(e) {
      e.preventDefault();
      // Get the canonical event key from the search box
      var canonical_search_term = $('#canonical-search-term').val();

      // Get the candidates from the database
      var req = $.ajax({
        url: $SCRIPT_ROOT + '/search_canonical',
        type: "POST",
        data: {
          canonical_search_term: canonical_search_term
        },
        beforeSend: function () {
          $('.flash').removeClass('alert-danger');
          $('.flash').addClass('alert-info');
          $('.flash').text("Loading...");
          $('.flash').show();
          }
      })
      .done(function() {
        // Update the canonical events in the search list
        $('#canonical-search-block').html(req.responseText);

        // Initialize the listeners for the new canonical search results
        initializeCanonicalSearchListeners();

        // get rid of loading flash 
        $('.flash').hide();
        $('.flash').removeClass('alert-info');
        return true;
      })
      .fail(function() { return makeError(req.responseText); });      
    });

    // initialize the grid and search 
    let search_params = new URLSearchParams(window.location.search);
    var repeated_fields = [
      'adj_filter_compare',
      'adj_filter_value',
      'adj_filter_field',
      'adj_sort_field',
      'adj_sort_order'
    ];
    var search_ids = ['adj_search_input'];

    // create indexed array of search parameters
    for(var i = 0; i < 3; i++) {
      for (var j = 0; j < repeated_fields.length; j++) {
        var field = repeated_fields[j] + '_' + i;
        search_ids.push(field);
      }
    }

    // initialize the search parameters in the URLs
    for(var i = 0; i < search_ids.length; i++) {
      $('#' + search_ids[i]).val(search_params.get(search_ids[i]));
    }

    loadSearch();
    loadGrid(
      search_params.get('canonical_event_key'),      
      search_params.get('cand_events')
    );
});