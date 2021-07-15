$(function(){ 
	$('#generate-ec').click(function (e){
	    req = $.ajax({
	      type: "POST",
	      url:  $SCRIPT_ROOT + '/_generate_coder_stats',
	      data: {
	        'pn': 'ec',
	        'action': 'save'
	      }
	    });

	    req.done(function() {
	        $('#coder-audit-form-group').removeClass('has-error');
	        $('#coder-audit-form-group').addClass('has-success');
	        $('#coder-audit-form-group div.form-control-feedback').html('File generated at <b>' 
	            + req.responseJSON['result']['filename'] + '</b>.');
	    });

	    req.fail(function() {
	        $('#coder-audit-form-group').removeClass('has-success');
	        $('#coder-audit-form-group').addClass('has-error');
	        $('#coder-audit-form-group div.form-control-feedback').text(req.responseText);
	    });
	});
});
