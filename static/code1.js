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
  $('#' + hash).click(deleteCode1);

  // show the list if it's hidden
  collapseDown(e, v);
}

var addCode = function(e, v) {
  var oText  = '';
  var tStart = 0;
  var tEnd   = 0;
  var el     = '';
  var aid    = $(".article").attr("id").split("_");

  // the various methods of getting the text object
  if (window.getSelection) {
      oText = window.getSelection();
  } else if (document.selection) {
      oText = document.selection.createRange().text;
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
    url:  $SCRIPT_ROOT + '/_add_code/1',
    data: {
      article:  aid[1],
      variable: v, 
      value:    p_id,
      text:     text
    }
  });

  // add element or change tab color on success
  req.success(function() {
    $("#flash-error").hide();
    createListItem(e, v, p_id, text);
  });

  // on failure
  req.fail(function(e) {
    $("#flash-error").text = "Error adding item.";
    $("#flash-error").show();
  });
}

var deleteCode1 = function(e) {
  var r = confirm("Are you sure you want to delete this item?");
  if (r == false) {
    return
  }

  // del_var_value
  a       = e.target.id.split("_");
  var aid = $(".article").attr("id").split("_");

  req = $.ajax({
    type: "GET",
    url:  $SCRIPT_ROOT + '/_del_code/1',
    data: {
      article:  aid[1],
      variable: a[1],
      value:    a[2]
    }
  });

  // on success, remove HTML element
  req.success(function() {
      $('#flash-error').hide();
      $(e.target).parent().remove();
  });

  req.fail(function() {
    $("#flash-error").text("Error deleting item.");
    $("#flash-error").show();
  });
}


function generate_handler( v, type ) {
  return function(e) { 
    var el = $(e.target);
    
    if(type == 'add') {
      addCode(e, v);
    } else if (type == 'collapse-down') {
      collapseDown(e, v);
    } else if (type == 'collapse-up') {
      collapseUp(e, v);
    }
  };
}

function generate_dd_listener(dd) {
  var aid  = $(".article").attr("id").split("_");
  return function(e) {
    var v = $('#' + dd).val();
    req = $.ajax({
      type: "POST",
      url:  $SCRIPT_ROOT + '/_add_code/1',
      data: {
        article:  aid[1],
        variable: dd,
        value:    v
      }
    });

    req.success(function(e) {
      $('#flash-error').hide();

      // show/hide var list for protest
      if(dd == 'protest') {
        if (v == 'yes' || v == 'maybe') {
          $('#varselect').show();
        } else {
          $('#varselect').hide();
        }
      }
    });

    req.fail(function(e) {
      $("#flash-error").text("Error changing " + dd);
      $("#flash-error").show();
    });
  }
}

$(function(){ // document ready
  var vars = []
  var dds  = ['protest', 'multi', 'nous'];
  var aid  = $(".article").attr("id").split("_");

  // Get vars from DOM  
  $('.varblock').each(function() {
    var i = $(this).attr("id").split("_")[1];
    vars.push(i); 
  });

  // prepopulate existing fields
  req = $.ajax({
      type: "GET",
      url:  $SCRIPT_ROOT + '/_get_codes',
      data: {
        article: aid[1]
      }
  });

  req.success(function(cd) {
    // turn the ignore text into re-add if this exists
    if(cd['ignore']) {
      $('p#readdDiv').show();
      $('p#ignoreDiv').hide();
    }

    // change protest dropdown and show vars
    if(cd['protest']) {
      $('[name=protest]').val(cd['protest']);

      if(cd['protest'] == 'yes' || cd['protest'] == 'maybe') {
        $('#varselect').show();
      }
    }

    // set multi
    if(cd['multi']) {
      $('[name=multi]').val(cd['multi']);
    }

    if(cd['nous']) {
      $('[name=nous]').val(cd['nous']);
    }

    // show comments
    if(cd['comments']) {
      $("#comments").val(cd['comments']);
    }

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

  // listen for typing
  $("#comments").keydown(function() {
    $("#unsaved").show();
  });

  // listen for comments and commit to DB
  $('#savecomments').click(function() {
    req = $.ajax({
      type: "POST",
      url:  $SCRIPT_ROOT + '/_add_code/1',
      data: {
        article:  aid[1],
        variable: "comments",
        value:    $("#comments").val()
      }
    });

    req.success(function(e) {
      $("#unsaved").hide();
      $('#flash-error').hide();
    });

    req.fail(function(e) {
      $("#flash-error").text("Error saving comments.");
      $("#flash-error").show();
    });
  });

  // generate add and collapse listeners
  for (i = 0; i < vars.length; i++) {
    var v       = vars[i];
    var actions = ['add', 'collapse-down', 'collapse-up'];

    for (j = 0; j < actions.length; j++) {
      var type = actions[j];
      $('#' + type + '_' + v).click( generate_handler( v, type ) );
    }
  }

  // TK: Hide all
  // create listeners for drop-downs
  for (i = 0; i < dds.length; i++) {
    var dd = dds[i];
    $('#' + dd).change( generate_dd_listener(dd) );
  }

  // Add listener for ignore button
  $('a#ignore').click(function(e) {
    var r = confirm("Are you sure you want to ignore this article?");
    if (r == false) {
      return
    }

    req = $.ajax({
      type: "POST",
      url:  $SCRIPT_ROOT + '/_add_code/1',
      data: {
        article:  aid[1],
        variable: "ignore",
        value:    0
      }
    });

    req.success(function(e) {
      $('#flash-error').hide();

      // redirect to next article
      setTimeout(function() {
        window.location.href = $('a#nextarticle').attr('href');
      }, 0);      
    });

    req.fail(function(e) {
      $("#flash-error").text("Error ignoring article.");
      $("#flash-error").show();
    });
  });

  // listener for re-add button
  $('a#readd').click(function(e) {
    var r = confirm("Are you sure you want to re-add this article?");
    if (r == false) {
      return
    }

    req = $.ajax({
      type: "GET",
      url:  $SCRIPT_ROOT + '/_del_code/1',
      data: {
        article:  aid[1],
        variable: "ignore",
        value:    0
      }
    });

    req.success(function(e) {
      $('#flash-error').hide();
      $('#ignoreDiv').show()
      $('#readdDiv').hide()
    });

    req.fail(function(e) {
      $("#flash-error").text("Error re-adding article.");
      $("#flash-error").show();
    });
  });  
});    
