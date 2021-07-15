/* Edit article-level info. */
var modifyArticleAnnotations = function() {
  var aid  = $(".article").attr("id").split("_")[1];
  var pn   = $('#pass_number').val();

  req = $.ajax({
      type: "GET",
      url:  $SCRIPT_ROOT + '/_load_article_annotation_block',
      data: {
        'article_id': aid,
        'pn': pn
      }
  });

  req.done(function() {
    $("#flash-error").hide();

    // add the article block to the HTML
    $('#article-annotation-blocks').append(req.responseText);

    // listeners for info radio buttons
    $('#article-annotation-block :radio').change(selectRadio);

    // listeners for text fields
    $('#article-annotation-block :text').blur(storeArticleTextInput);
    $('#article-annotation-block textarea').blur(storeArticleTextInput);

    // listeners for adding or deleting checkboxes
    $('#article-annotation-block :checkbox').change(selectArticleCheckbox);
  });

  req.fail(function(e) {
    $("#flash-error").text("Error loading article annotation block.");
    $("#flash-error").show();
  });
}

/* Add or edit an event. Controls the event list. */
var modifyEvent = function(e) {
  var aid  = $(".article").attr("id").split("_")[1];
  var eid  = e.target.id.split("_")[1];
  var pn   = $('#pass_number').val();
  var vars = [];

  // Load the block for creating event information.
  req = $.ajax({
      type: "GET",
      url:  $SCRIPT_ROOT + '/_load_event_block',
      data: {
        'article_id': aid,
        'event_id': eid,
        'pn': pn
      }
  });

  req.done(function() {
    $("#flash-error").hide();

    // remove all the event blocks
    $(".event-block").each(function() {
      $(this).remove();
    });

    // add the event block to the HTML
    $("#event-blocks").append(req.responseText);

    // date listeners
    $('#start-date-picker').datetimepicker({ format: 'YYYY-MM-DD' });
    $('#end-date-picker').datetimepicker({ format: 'YYYY-MM-DD' });

    // add tab listeners
    $(".tablinks").each(function(){
      $(this).click(changeTab);
    });

    // show basic info first
    $("#basicinfo_block").show();

    // add listeners for options
    $("#preset_block :radio").each(function() {
      $(this).change(function(e) {
        var variable = $(e.target).attr("id").split("_")[1];

        // hide everything
        $(".options").each( function() { $(this).hide() });

        // except options for currently selected variable
        $("#options_" + variable).show();
      });
    });

    // show 'form' options upon default
    $('#varevent_form').prop("checked", true);
    $("#options_form").show(); 

    // listeners for info radio buttons
    $('#yes-no_block :radio').change(selectRadio);

    // listeners for select drop-downs
    $('#basicinfo_block select').change(selectRadio);

    // listeners for text fields
    // $('#basicinfo_block :date').blur(storeText); // doesn't work in Firefox :(

    $('#basicinfo_block :text').blur(storeText);
    $('#basicinfo_block textarea').blur(storeText);

    // listener for actors-freeform
    $('#textselect_block textarea').blur(storeText);
      
    // listeners for adding or deleting checkboxes
    $('#basicinfo_block :checkbox').change(selectCheckbox);
    $('#yes-no_block :checkbox').change(selectCheckbox);
    $('#preset_block :checkbox').change(selectCheckbox);

    // Get text select vars from DOM  
    $('.varblock').each(function() {
      var i = $(this).attr("id").split("_")[1];
      vars.push(i); 
    });

    // load text selects with this
    // doing it like this because this function adds additional listeners
    req = $.ajax({
      type: "GET",
      url:  $SCRIPT_ROOT + '/_get_codes',
      data: {
        'article': aid,
        'event': eid,
        'pn': pn
      }
    });

    req.done(function(cd) {
      $("#flash-error").hide();
  
      // listeners for text select add, collapse-up/down
      for (i = 0; i < vars.length; i++) {
        var v = vars[i];
        var actions = ['add', 'collapse-down', 'collapse-up'];

        for (j = 0; j < actions.length; j++) {
          var type = actions[j];
          $('#' + type + '_' + v).on("click", generate_handler( v, type ) );
        }

        // add text select variable text
        if(cd[v]) {
          for(j = 0; j < cd[v].length; j++) {
            o = cd[v][j];
            createListItem('', v, o[0], o[1]);
          }
        }	  
      }
	
      // highlight the current event desc text box
      $('.event-desc').each(function() {
	  $(this).removeClass('selected');
      });

      $('#event-desc_' + eid).addClass('selected');
    });

    // listener for submit and save
    $("#save").click(function(e) {
        // remove all the event blocks
        $(".event-block").each(function() {
          $(this).remove();
        });

	// loads all the event blocks
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
    type: "POST",
    url:  $SCRIPT_ROOT + '/_del_event',
    data: {
      event: eid,
      pn: $('#pass_number').val()
    }
  });

  // on done, remove HTML element 
  // and the edit block if it exists
    req.done(function() {
	$('#flash-error').hide();
	$('div#event-item_' + eid).remove();
	$("#event-creator-block_" + eid).remove();
  });

  req.fail(function() {
    $("#flash-error").text("Error deleting item.");
    $("#flash-error").show();
  });
}

/* Loads the list of events and adds edit / delete listeners */
var getEvents = function(aid) {
  var pn  = $('#pass_number').val();
  var req = $.ajax({
      type: "GET",
      url:  $SCRIPT_ROOT + '/_get_events',
      data: {
        article_id: aid,
        pn: pn
      }
  });

  // on done -- add items to list
  req.done(function(ev) {
    events = ev['events'];

    // empty list
    $('#list-events').empty();

    // add existing events
    for(i = 0; i < events.length; i++) {
      var event_id   = events[i]['id'];
      var event_repr = events[i]['repr'];

      var date = new Date();

      // create datetime hashes for icons
      var min_hash = ["min", event_id, date.getTime()].join("_");	
      var edit_hash = ["edit", event_id, date.getTime()].join("_");
      var del_hash  = ["del", event_id, date.getTime()].join("_");

      // create elements
	var event = "<div id='event-item_" + event_id + "' class='event-item'>" +
	    "<div class='vartitle icons'><span>" + event_id + "</span> " +
//	    "<a id='" + min_hash + "' class='glyphicon glyphicon-chevron-down'></a> " +
	    "<a id='" + edit_hash + "' class='glyphicon glyphicon-pencil'></a> " +
	    "<a id='" + del_hash + "' class='glyphicon glyphicon-trash'></a>" +
	    "</div> " +
	    "<p id='event-desc_" + event_id + "' class='event-desc'>" + event_repr + "</p>" +
	    "</div>";

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

  getEvents(aid);

  // add event listener
  $('#add-event').click(modifyEvent);

  // test code for article block
  modifyArticleAnnotations()

  // mark done handler
  $('#mark-done').each(function() {
    $(this).click(function() {
      var req = $.ajax({
          type: "POST",
          url:  $SCRIPT_ROOT + '/_mark_ec_done',
          data: {
            article_id: aid
          }
      });  

      req.done(function(ev) {
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
