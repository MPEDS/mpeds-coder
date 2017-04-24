/* Add or edit an event. Controls the event list. */
var modifyEvent = function(e) {
  var aid = $(".article").attr("id").split("_")[1];
  var eid = e.target.parentElement.id.split("_")[1];
  req = $.ajax({
      type: "GET",
      url:  $SCRIPT_ROOT + '/_load_event_block',
      data: {
        'article_id': aid,
        'event_id': eid
      }
  });

  req.success(function(ev) {
    $("#flash-error").hide();

    // add the event block to the HTML
    $("#event-blocks").append(req.responseText);

    // add listeners for options
    $(".event-block :radio").each(function() {
      $(this).change(function(e) {
        var variable = $(e.target).attr("id").split("_")[1];

        // hide everything
        $(".options").each( function() { $(this).hide() });

        // except options for currently selected variable
        $("#options_" + variable).show();
      });

      // set eid here for adding new events
      eid = $(".event-block").attr("id").split("_")[1];
    });

    // listeners for adding or deleting checkboxes
    $(':checkbox').change(selectCheckbox);

    // listener to add code
    $('.event-block label a').click(addCode);

    // listener for submit and save
    $("#add-event-block").click(function(e) {
      var event_id = $(e.target).parent().attr("id").split("_")[1];

      // save comments
      var comments = $('#eventblock_' + event_id + ' #comments').val();
      req = $.ajax({
        type: "GET",
        url:  $SCRIPT_ROOT + '/_add_code/2',
        data: {
          article:  aid,
          variable: "comments",
          value:    comments,
          event:    event_id
        }
      });

      req.success(function(e) {
        $('#flash-error').hide();
      });

      req.fail(function(e) {
        $("#flash-error").text("Error adding comments.");
        $("#flash-error").show();
      });

      // remove all the event blocks
      $(".event-block").each(function() {
        $(this).remove();
      });

      getEvents(aid);
    });
  });

  req.fail(function(e) {
    $("#flash-error").text("Error loading event block.");
    $("#flash-error").show();
  }); 
}

/* Deletes an event on clicking the remove button. */
var deleteEvent = function(e) {
  var aid = $(".article").attr("id").split("_")[1];
  var eid = e.target.id.split("_")[1];

  var r = confirm("Are you sure you want to delete this item?");
  if (r == false) {
    return
  }

  req = $.ajax({
    type: "GET",
    url:  $SCRIPT_ROOT + '/_del_event',
    data: {
      event: eid
    }
  });

  // on success, remove HTML element 
  // and the edit block if it exists
  req.success(function() {
      $('#flash-error').hide();
      $(e.target).parent().remove();
      $("#eventblock_" + eid).remove();
  });

  req.fail(function() {
    $("#flash-error").text("Error deleting item.");
    $("#flash-error").show();
  });
}

/* Loads the list of events upload page load and adding a new event. */
var getEvents = function(aid) {
  var req = $.ajax({
      type: "GET",
      url:  $SCRIPT_ROOT + '/_get_events',
      data: {
        article_id: aid
      }
  });

  // on success -- add items to list
  req.success(function(ev) {
    events = ev['events'];

    // empty list
    //$('#list-events').empty();

    // add existing events
    for(i = 0; i < events.length; i++) {
      var event_id   = events[i]['id'];
      var event_repr = events[i]['repr'];

      var date = new Date();

      // create a datetime hashes
      var edit_hash = ["edit", event_id, date.getTime()].join("_");
      var del_hash  = ["del", event_id, date.getTime()].join("_");

      // create elements
      var event = "<p id='listevent_" + event_id + "'>" + event_id + ": " + event_repr + " <a id='" + edit_hash + "' class='glyphicon glyphicon-pencil'></a> <a id='" + del_hash + "' class='glyphicon glyphicon-remove'></a></p>";

      // add new events
      $('#list-events').append(event);

      // create a listener for the edit and delete buttons
      $('#' + edit_hash).click(modifyEvent);
      $('#' + del_hash).click(deleteEvent);
    }
  });
 
  req.fail(function(e) {
    $("#flash-error").text("Error loading stored events.");
    $("#flash-error").show();
  });
}

/* Adds a value for a variable if not available in the current list. */
var addCode = function(e) {
  var oText    = '';
  var aid      = $(".article").attr("id").split("_")[1];
  var eid      = $(e.target).closest(".event-block").attr("id").split("_")[1];
  var variable = e.target.parentElement.id.split("_")[2];

  // the various methods of getting the text object
  if (window.getSelection) {
      oText = window.getSelection();
  } else if (document.selection) {
      oText = document.selection.createRange().text;
  } else if (document.getSelection) {
      oText = document.getSelection();
  }

  text  = oText.toString().trim();
  // skip when there is nothing selected
  if (text.length <= 0) {
    return;
  }

  req = $.ajax({
    type: "GET",
    url:  $SCRIPT_ROOT + '/_add_code/2',
    data: {
      article:  aid,
      variable: variable,
      value:    text,
      event:    eid
    }
  });

  // add element or change tab color on success
  req.success(function() {
    $("#flash-error").hide();

    // create element
    var li = '<input type="checkbox" id="dd_' + variable + '_' + text + '" checked /> <label for="dd_' + variable + '_' + text + '">' + text + '</label><br />';

    // add to the list
    $('#options_' + variable).append(li);

    // create a listener for the checkbox
    $('#dd_' + variable + '_' + text).click(selectCheckbox);
  });

  // on failure
  req.fail(function(e) {
    $("#flash-error").text = "Error adding item.";
    $("#flash-error").show();
  });
}

var changeTab = function(e) {
    var eid = $(e.target).parent().attr("id").split("_")[0];

    // Get all elements with class="tablinks" and remove the class "active"
    $(".tablinks").each(function() {
      $(this).removeClass('active')
    });

    // hide all other tab content
    $(".tab-pane").each(function() {
      $(this).hide();
    });

    // Show the current tab, and add an "active" class to the button that opened the tab
    $('#' + eid + "_button").addClass("active");
    $('#' + eid + "_block").show();
}

// MAIN -- document ready 
$(function(){ 
  var aid = $(".article").attr("id").split("_")[1];

  // add tab listeners
  $(".tablinks").each(function(){
    $(this).click(changeTab);
  });

  // show basic info first
  $("#basicinfo_block").show();

  getEvents(aid);

  // add event listener
  $('#add-event-btm').click(modifyEvent);

  // mark done
  $('#mark-done').each(function() {
    $(this).click(function() {
      var req = $.ajax({
          type: "GET",
          url:  $SCRIPT_ROOT + '/_mark_sp_done',
          data: {
            article_id: aid
          }
      });  

      req.success(function(ev) {
        $("#flash-error").hide();

        // go to next
        window.location.assign($SCRIPT_ROOT + '/event_creator');
      });

      req.fail(function(e) {
        $("#flash-error").text("Error going to next article.");
        $("#flash-error").show();
      }); 
    }); 
  });

});    