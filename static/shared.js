var collapseDown = function(e, v) {
  $('#collapse-down_' + v).hide();
  $('#list_' + v).show();
  $('#collapse-up_' + v).show();
}

var collapseUp = function(e, v) {
  $('#list_' + v).hide();
  $('#collapse-up_' + v).hide();
  $('#collapse-down_' + v).show();
}

var createListItem = function(e, v, p_id, text) {
  displayText = text;

  // truncate in display
  if (text.length > 40) {
    displayText = text.substr(0, 20) + " ... " + text.substr(text.length - 20, text.length);
  }

  // change color of paragraph link
  var date = new Date();
  
  // create a datetime hash for the delete ID
  var hash = ["del", v, p_id, date.getTime()].join("_");

  // create element
  var li = "<p id='" + p_id + "'>" + displayText + " <a id='" + hash + "' class='glyphicon glyphicon-remove'></a></p>";

  // add to the list
  $('#list_' + v).append(li);

  // create a listener for the delete button
  $('#' + hash).click(deleteCode);

  // show the list if it's hidden
  collapseDown(e, v);
}

var addSelectedText = function(e, v) {
  var oText  = "";
  var tStart = 0;
  var tEnd   = 0;
  var el     = '';
  var aid    = $(".article").attr("id").split("_");
  var pn     = $('#pass_number').val();
  var ev_id  = $(e.target).closest('div.event-block').attr('id').split("_")[1];

  // the various methods of getting the text object
  if (window.getSelection) {
      oText = window.getSelection();
  } else if (document.getSelection) {
      oText = document.getSelection();
  }

  text  = oText.toString().trim();
  if (text.length > 0) {
    // get paragraph and range
    tPara  = oText.anchorNode.parentElement.id;
    // paragraph is sometimes null, so label as 0
    if(tPara == '') {
      tPara = 0
    }

    // anchorOffset is where selecting begins
    // focusOffset is where it ends
    // the start should be the one that is lower
    if (oText.anchorOffset < oText.focusOffset) {
      tStart = oText.anchorOffset;
    } else {
      tStart = oText.focusOffset;
    }

    tEnd = tStart + text.length;

    // create paragraph id with relevant info
    p_id = tPara + "-" + tStart + "-" + tEnd;
  } else {
    return;
  }

  req = $.ajax({
    type: "POST",
    url:  $SCRIPT_ROOT + '/_add_code/' + pn,
    data: {
      article:  aid[1],
      variable: v, 
      value:    p_id,
      text:     text,
      event:    ev_id
    },
  });

  // add element or change tab color on done
  req.done(function() {
    $("#flash-error").hide();
    createListItem(e, v, p_id, text);
  });

  // on failure
  req.fail(function(e) {
    $("#flash-error").text = "Error adding item.";
    $("#flash-error").show();
  });
}

var deleteCode = function(e) {
  var r = confirm("Are you sure you want to delete this item?\n(Note: due to bug, duplicates will not be deleted)");
  if (r == false) {
    return
  }

  var a   = e.target.id.split("_");
  var aid = $(".article").attr("id").split("_");
  var pn  = $('#pass_number').val();
  var ev  = $(e.target).closest('div.event-block').attr('id').split("_")[1];

  req = $.ajax({
    type: "POST",
    url:  $SCRIPT_ROOT + '/_del_code/' + pn,
    data: {
      article:  aid[1],
      variable: a[1],
      value:    a[2],
      event:    ev
    }
  });

  // on done, remove HTML element
  req.done(function() {
      $('#flash-error').hide();
      $(e.target).parent().remove();
  });

  req.fail(function() {
    $("#flash-error").text("Error deleting item." + req.responseText);
    $("#flash-error").show();
  });
}

/* Adds a value for a variable if not available in the current list. */
// DS 2020-01-16: Looks like this is only used by code1.js and code2.js
var addCode = function(e) {
  var oText    = '';
  var aid      = $(".article").attr("id").split("_")[1];
  var eid      = $(e.target).closest(".event-block").attr("id").split("_")[1];
  var pn       = $('#pass_number').val();
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
    type: "POST",
    url:  $SCRIPT_ROOT + '/_add_code/' + pn,
    data: {
      article:  aid,
      variable: variable,
      value:    text,
      event:    eid
    }
  });

  // add element or change tab color on done
  req.done(function() {
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

var generate_handler = function( v, type ) {
  return function(e) { 
    var el = $(e.target);
    
    if(type == 'add') {
      addSelectedText(e, v);
    } else if (type == 'collapse-down') {
      collapseDown(e, v);
    } else if (type == 'collapse-up') {
      collapseUp(e, v);
    }
  };
}

/* Adds or deletes values for article variables based on checkboxes. */
var selectArticleCheckbox = function(e) {
  var el       = $(e.target);
  var aid      = $(".article").attr("id").split("_")[1];  
  var pn       = $('#pass_number').val();

  var variable = el.attr("id").split("_")[1];
  var val      = el.val();

  // for some of the basic info variables, id == val. change to 'yes'
  if (variable == val) {
    val = 'yes';
  }

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
    url:  $SCRIPT_ROOT + '/_' + action + '_article_code/' + pn,
    data: {
      article:  aid,
      variable: variable,
      value:    val
    }
  });

  req.done(function(e) {
    $('#flash-error').hide();
  });

  req.fail(function(e) {
    $("#flash-error").text("Error changing checkbox.");
    $("#flash-error").show();
  });
}

/* Adds or deletes values for each event variable based on checkboxes. */
var selectCheckbox = function(e) {
  var el       = $(e.target);
  var aid      = $(".article").attr("id").split("_")[1];  
  var eid      = el.closest(".event-block").attr("id").split("_")[1];
  var pn       = $('#pass_number').val();

  var variable = el.attr("id").split("_")[1];
  var val      = el.val();

  // for some of the basic info variables, id == val. change to 'yes'
  if (variable == val) {
    val = 'yes';
  }

  var is_checked = el.is(':checked');
  var action = ''

  // add this checkbox item
  if (is_checked == true) {
    action = 'add';
  } else { // delete it
    action = 'del';
  }

  req = $.ajax({
    type: "POST",
    url:  $SCRIPT_ROOT + '/_' + action + '_code/' + pn,
    data: {
      article:  aid,
      variable: variable,
      value:    val,
      event:    eid
    }
  });

  req.done(function(e) {
    $('#flash-error').hide();
  });

  req.fail(function(e) {
    $("#flash-error").text("Error changing checkbox.");
    $("#flash-error").show();
  });
}

/* Adds or deletes values for each variable based on radio buttons selected. */
/* Also handles select controls */
var selectRadio = function(e) {
  var el       = $(e.target);
  var aid      = $(".article").attr("id").split("_")[1];  
  var eid      = el.closest(".event-block").attr("id").split("_")[1];
  var pn       = $('#pass_number').val();

  var variable = el.attr("id").split("_")[1];
  var val      = el.val();

  // change code
  req = $.ajax({
    type: "POST",
    url:  $SCRIPT_ROOT + '/_change_code/' + pn,
    data: {
      article:  aid,
      variable: variable,
      value:    val,
      event:    eid
    }
  });

  req.done(function(e) {
    $('#flash-error').hide();
  });

  req.fail(function(e) {
    $("#flash-error").text("Error changing radio button or drop-down.");
    $("#flash-error").show();
  });
}

/* Adds or deletes values for each variable based on radio buttons selected. */
var storeArticleTextInput = function(e) {
  var el       = $(e.target);
  var aid      = $(".article").attr("id").split("_")[1];  
//  var eid      = el.closest(".event-block").attr("id").split("_")[1];
  var pn       = $('#pass_number').val();

  var variable = el.attr("id").split("_")[1];
  var val      = el.val();

  // change code
  req = $.ajax({
    type: "GET",
    url:  $SCRIPT_ROOT + '/_change_article_code/' + pn,
    data: {
      article:  aid,
      variable: variable,
      value:    val //,
//      event:    eid
    }
  });

  req.done(function(e) {
    $('#flash-error').hide();
  });

  req.fail(function(e) {
    $("#flash-error").text("Error changing article text input.");
    $("#flash-error").show();
  });
}

/* Adds or deletes values for each variable based on radio buttons selected. */
var storeText = function(e) {
  var el       = $(e.target);
  var aid      = $(".article").attr("id").split("_")[1];  
  var eid      = el.closest(".event-block").attr("id").split("_")[1];
  var pn       = $('#pass_number').val();

  var variable = el.attr("id").split("_")[1];
  var val      = el.val();

  // change code
  req = $.ajax({
    type: "POST",
    url:  $SCRIPT_ROOT + '/_change_code/' + pn,
    data: {
      article:  aid,
      variable: variable,
      value:    val,
      event:    eid
    }
  });

  req.done(function(e) {
    $('#flash-error').hide();
  });

  req.fail(function(e) {
    $("#flash-error").text("Error changing radio button.");
    $("#flash-error").show();
  });
}

// DS 2020-01-16: it looks like nothing anywhere calls this?
var getCodes = function(ev) {
  // prepopulate existing fields
  var aid = $(".article").attr("id").split("_")[1];    
  var pn  = $("#pass_number").val();

  req = $.ajax({
      type: "GET",
      url:  $SCRIPT_ROOT + '/_get_codes',
      data: {
        article: aid[1],
        event: ev,
        pn: pn
      }
  });

  req.done(function(cd) {
    // add existing variable text
    for(i = 0; i < vars.length; i++) {
      v = vars[i];
      if(cd[v]) {
        for(j = 0; j < cd[v].length; j++) {
          o = cd[v][j];
          createListItem('', v, o[0], o[1]);
        }
      }
    }
  });

  req.fail(function(e) {
    $("#flash-error").text("Error loading stored data.");
    $("#flash-error").show();
  });
}


$(function(){ // document ready
  // keep sticky coding at the top 
  if (!!$('.sticky').offset()) { // make sure [".sticky" element exists
    var stickyTop = $('.sticky').offset().top; // returns number 

    $(window).scroll(function(){ // scroll event
      var windowTop = $(window).scrollTop(); // returns number 
      if (stickyTop < windowTop){
        $('.sticky').css({ position: 'fixed', top: 0 });
      } else {
        $('.sticky').css('position','static');
      }
    });
  }

    // create listeners for drop-downs
  // for (i = 0; i < dds.length; i++) {
  //   var dd = dds[i];
  //   $('#' + dd).change( generate_dd_listener(dd) );
  // }
});
