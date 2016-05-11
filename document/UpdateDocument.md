# Updates Document
## Paging & Searching
### Paging Solution 1
Github Commit: https://github.com/alexhanna/mpeds-coder/commit/854cf1f66f71fa73f22a36abb9b029837d5d4fe1
Main Idea:  The first change is adding a function called `paginate`. It takes four parameters:
- `query` : The sql alchemy query object.
- `page` : The current page number.
- `per_page`: How many item shows per page.
- `error_out`: Whether show error page.
Then it will using limit and offset of the query object to query the items in the page. and return a
`Pagination` object.

`Pagination` is defined to maintain the status of the page and return the current page item and construct
HTML for each page. It is extracted from the flask-sqlalchemy, this class receive
a sqlalchemy object and provide next, prev function and other properties for get the page content.
In next, prev implementation, it called `paginate` to query the next and prev page.
The properties of prev_num, has_next, next_num, has_prev is for getting the status of the current page.

The `iter_pages` method is the helper method for the template to call to generate the HTML in the template.

To use the new added function and class is pretty easy, just wrap the previous return object with the
`paginate` function, and it returns a pagination object. Them pass the pagination object to the template.


In the template, I added `render_pagination` macro and take the `pagination` object to get the
 status of current page and generate the HTML.

DrawBack: Doesn't support search.

### Paging Soltion 2

Using jQuery plugin: datatable.
Using it is pretty easy:
```javascript
$(document).ready(function() {
    $('#code2queue').DataTable( {
      "pageLength":25
    } );
} );
```

I added code2queue.js and list.js and adding this
code in. Then it could wrap the table with pagination
and search.

Drawback: It actually load all table data in one time
and page it in local. To make it auto load from the
server need implement the ajax API for it. I didn't
do this.


## Admin Panel

The Admin Panel is mainly based on a free template called
minimal_admin_panel. I put it in the document too.
It is based on bootstrap3 and has detailed example pages.
Just check it out and grab the style in it.

The changes I have made is support those js and css
in our template by adding url_for() function in the template
and generate the right javascript page.

I also modified the style.css file to make it show better.


## Dynamic Form

Dynamic Form implementation is mainly based on jsonform.js
The playground and documention for it can be found at:
[jsonform](http://ulion.github.io/jsonform/playground/)

The main changes I have made is adding the new type of the
form component.

The changes can be find in these to commit:
- https://github.com/alexhanna/mpeds-coder/commit/930e66b5f16ab75543a18735e062d2ecbf074a72
- https://github.com/alexhanna/mpeds-coder/commit/e0f99bff3de0cb8cff0d52e1fc34dd3cde620125

The updated file is in: static/js/jsonform.js

The adding method is to change the `jsonform.elementTypes`,
which the jsonform will use it to query the name specified
in the json schema. I added two new type: `highlightlist`,
`ignoreButton`, which have the represent ajax call in the
original code.

