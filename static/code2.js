/* Adds or deletes values for each variable based on checkboxes. */
var selectCheckbox = function(e) {
  var el  = $(e.target);
  var aid = $(".article").attr("id").split("_")[1];  
  var sid = el.attr("id").split("_");
  var val = $("label[for='" + el.attr('id') + "']").text();
  var eid = $(e.target).closest(".event-block").attr("id").split("_")[1];

  var is_checked = el.is(':checked');
  var action = ''

  // add this checkbox item
  if (is_checked == true) {
    action = 'add';
  } else { // delete it
    action = 'del';
  }

  req = $.ajax({
    type: "GET",
    url:  $SCRIPT_ROOT + '/_' + action + '_code/2',
    data: {
      article:  aid,
      variable: sid[1],
      value:    val,
      event:    eid
    }
  });

  req.success(function(e) {
    $('#flash-error').hide();
  });

  req.fail(function(e) {
    $("#flash-error").text("Error changing checkbox.");
    $("#flash-error").show();
  });
}

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
    $("#submit").click(function(e) {
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
    $('#list-events').empty();

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

$(function(){ // document ready
  var aid = $(".article").attr("id").split("_")[1];

  getEvents(aid);

  // add event listener
  $('#add-event').click(modifyEvent);

  // mark done
  $('.mark-done').each(function() {
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
        window.location.assign($SCRIPT_ROOT + '/code2');
      });

      req.fail(function(e) {
        $("#flash-error").text("Error going to next article.");
        $("#flash-error").show();
      }); 
    }); 
  });

  // Add listener for ignore button
  $('a#ignore').click(function(e) {
    var r = confirm("Are you sure you want to ignore this article?");
    if (r == false) {
      return
    }

    req = $.ajax({
      type: "GET",
      url:  $SCRIPT_ROOT + '/_add_code/2',
      data: {
        article:  aid,
        variable: "ignore",
        value:    0
      }
    });

    req.success(function(e) {
      $('#flash-error').hide();

      var req = $.ajax({
          type: "GET",
          url:  $SCRIPT_ROOT + '/_mark_sp_done',
          data: {
            article_id: aid
          }
      });  

      req.success(function(ev) {
        // go to next
        window.location.assign($SCRIPT_ROOT + '/code2');
      }); 

      req.fail(function(e) {
        $("#flash-error").text("Error ignoring article and moving to next.");
        $("#flash-error").show();
      });
    });

    req.fail(function(e) {
      $("#flash-error").text("Error ignoring article.");
      $("#flash-error").show();
    });
  });

  // on radio button change, highlight text
  $('#secondpassinfo :radio').change(function() {
    // get coder and variable
    var variable = $("input[name=var]:checked").val()

    req = $.ajax({
      type: "GET",
      url:  $SCRIPT_ROOT + '/_highlight_var',
      data: {
        article:  aid,
        variable: variable
      }
    });

    req.fail(function(e) {
      $("#flash-error").text("Error selecting variable.");
      $("#flash-error").show();
      return;
    });

    // on success, show text + highlighting
    req.success(function(e) {
      $('#flash-error').hide();
      $('#meta').html(req['responseJSON']['result']['meta']);
      $('#bodytext').html(req['responseJSON']['result']['body']);
    });
  });
});    