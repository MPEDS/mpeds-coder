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

var addUser = function(e) {
    var username = $('#username').val();
    req = $.ajax({
      type: "GET",
      url:  $SCRIPT_ROOT + '/_add_user',
      data: {
        'username': username
      }
    });

    req.success(function() {
    $('#username-form-group').removeClass('has-error');            

    $('#username-form-group').addClass('has-success');
    $('#username-form-group div.form-control-feedback').html('User <b>' 
        + username + '</b> created. Their password is <b>' 
        + req.responseJSON['result']['password'] + '</b>. ' + 
        'Please save this.');
    });

    req.fail(function() {
      $('#username-form-group').removeClass('has-success');            

      $('#username-form-group').addClass('has-error');
      $('#username-form-group div.form-control-feedback').text(req.responseText);
    });
}


var assignArticles = function(e) {
    var num   = $('#num-articles').val();
    var db    = $('#article-database').val();
    var users = [];

    // gets the checkbox
    var same  = $('input[name=article-distribution]:checked').val();

    // gets all the checked users
    $('div#assign-articles_block input.user:checked').each(function() {
        users.push($(this).val());
    });

    req = $.ajax({
      type: "GET",
      url:  $SCRIPT_ROOT + '/_assign_articles',
      data: {
        'num': num,
        'db': db,
        'users': users.join(),
        'same': same
      }
    });

    req.success(function() {
        $('#assign-articles-form-group').removeClass('has-error');            

        $('#assign-articles-form-group').addClass('has-success');
        $('#assign-articles-form-group div.form-control-feedback').text(req.responseText);
    });

    req.fail(function() {
        $('#assign-articles-form-group').removeClass('has-success');            

        $('#assign-articles-form-group').addClass('has-error');
        $('#assign-articles-form-group div.form-control-feedback').text(req.responseText);
    });

}


$(function(){ 
    // add tab listeners
    $(".tablinks").each(function(){
      $(this).click(changeTab);
    });

    // show add user first
    $("#add-user_block").show();

    $('#submit').click(function(e) {
        // get the active button to identify correct form
        var current_form = $('.active').attr("id").split('_')[0];

        // create user
        if (current_form == 'add-user') {
            addUser(e);
        } else if (current_form == 'assign-articles') {
            assignArticles(e);
        }
    });
});