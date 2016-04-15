/**
 * Created by baiyijing on 3/29/16.
 */

$(document).ready(function () {
    var editor = ace.edit("editor");
    editor.getSession().setMode("ace/mode/json");
    
    var generator = new formGeneator();
    editor.getSession().on("change", function(e) {
        generator.generateForm(editor.getSession().getValue());
    });

    generator.generateForm(editor.getSession().getValue());
    
    function formGeneator() {
        /**
           * Displays the form entered by the user
           * (this function runs whenever once per second whenever the user
           * changes the contents of the ACE input field)
           */
        this.generateForm = function (formValue) {
            var values = formValue;

            // Reset result pane
            $('#result').html('');

            // Parse entered content as JavaScript
            // (mostly JSON but functions are possible)
            var createdForm = null;
            try {
              // Most examples should be written in pure JSON,
              // but playground is helpful to check behaviors too!
              eval('createdForm=' + values);
            }
            catch (e) {
              $('#result').html('<pre>Entered content is not yet a valid' +
                ' JSON Form object.\n\nJavaScript parser returned:\n' +
                e + '</pre>');
              return;
            }

            // Render the resulting form, binding to onSubmitValid
            try {
              createdForm.onSubmitValid = function (values) {
                if (console && console.log) {
                  console.log('Values extracted from submitted form', values);
                }
                window.alert('Form submitted. Values object:\n' +
                  JSON.stringify(values, null, 2));
              };
              createdForm.onSubmit = function (errors, values) {
                if (errors) {
                  console.log('Validation errors', errors);
                  return false;
                }
                return true;
              };
              $('#result').html('<form id="result-form" class="form-vertical"></form>');
              $('#result-form').jsonForm(createdForm);
            }
            catch (e) {
              $('#result').html('<pre>Entered content is not yet a valid' +
                ' JSON Form object.\n\nThe JSON Form library returned:\n' +
                e + '</pre>');
              return;
            }
          };   
    }
   
    
    
})