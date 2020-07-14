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
      type: "POST",
      url:  $SCRIPT_ROOT + '/_add_user',
      data: {
        'username': username
      }
    });

    req.done(function() {
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
    var num        = $('#num-assign-articles').val();
    var db         = $('#article-database').val();
    var pub        = $('#assign-articles-publication').val();
    var ids        = $('#assign-articles-ids').val();
    var users      = [];
    var group_size = $('#group-size').val();

    // gets the checkbox
    var same = $('input[name=article-distribution]:checked').val();

    // gets all the checked users
    $('#individual-users input.user:checked').each(function() {
        users.push($(this).val());
    });

    req = $.ajax({
      type: "POST",
      url:  $SCRIPT_ROOT + '/_assign_articles',
      data: {
        'num':        num,
        'db':         db,
        'pub':        pub,
        'ids':        ids,
        'users':      users.join(),
        'same':       same,
        'group_size': group_size
      }
    });

    req.done(function() {
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

var transferArticles = function(e) {
    var num        = $('#num-transfer-articles').val();
    var from_users = [];
    var to_users   = [];

    // gets all the checked users
    $('#from-users input:checked').each(function() {
        from_users.push($(this).val());
    });

    $('#to-users input:checked').each(function() {
        to_users.push($(this).val());
    });

    req = $.ajax({
      type: "GET",
      url:  $SCRIPT_ROOT + '/_transfer_articles',
      data: {
        'num': num,
        'from_users': from_users.join(),
        'to_users': to_users.join()
      }
    });

    req.done(function() {
        $('#transfer-articles-form-group').removeClass('has-error');            
        $('#transfer-articles-form-group').addClass('has-success');
        $('#transfer-articles-form-group div.form-control-feedback').text(req.responseText);
    });

    req.fail(function() {
        $('#transfer-articles-form-group').removeClass('has-success');            
        $('#transfer-articles-form-group').addClass('has-error');
        $('#transfer-articles-form-group div.form-control-feedback').text(req.responseText);
    });
}

var searchSolr = function(e) {
    req = $.ajax({
        type: "GET",
        url: $SCRIPT_ROOT + '/_search_solr',
        data: {
            'database'      : $('#database').val(),
            'publication'   : $('#publication').val(),
            'start-date'    : $('#start-date').val(),
            'end-date'      : $('#end-date').val(),
            'search-string' : $('#search-string').val(),
            'solr-ids'      : $('#solr-ids').val()
        }
    });

    req.done(function() {
        $('#search-solr-form-group').removeClass('has-error');            
        $('#search-solr-form-group').addClass('has-success');
        $('#search-solr-form-group div.form-control-feedback').text(req.responseText);
    });

    req.fail(function() {
        $('#search-solr-form-group').removeClass('has-success');            
        $('#search-solr-form-group').addClass('has-error');
        $('#search-solr-form-group div.form-control-feedback').text(req.responseText);
    });

}

$(function(){ 
    // add tab listeners
    $(".tablinks").each(function(){
      $(this).click(changeTab);
    });

    // show add user first
    $("#add-user_block").show();

    // date listeners
    $('#start-date-picker').datetimepicker({ format: 'YYYY-MM-DD' });
    $('#end-date-picker').datetimepicker({ format: 'YYYY-MM-DD' });

    $('#submit').click(function(e) {
        // get the active button to identify correct form
        var current_form = $('.active').attr("id").split('_')[0];

        // create user
        if (current_form == 'add-user') {
            addUser(e);
        } else if (current_form == 'assign-articles') {
            assignArticles(e);
        } else if (current_form == 'transfer-articles') {
            transferArticles(e);
        } else if (current_form == 'search-solr') {
            searchSolr(e);
        }
    });
});
