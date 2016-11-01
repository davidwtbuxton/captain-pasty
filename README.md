Captain Pasty
=============

A pastebin on Google App Engine's Python runtime. It looks a bit like GitHub's Gist.


Installation
------------

You must install the App Engine SDK yourself. Then install Captain Pasty and its dependencies.

    $ git clone https://github.com/davidwtbuxton/captain-pasty.git
    $ cd captain-pasty
    $ ./installdeps.sh

Update the CSS:

    $ npm run build && npm run watch

Run the development server:

    $ python manage.py runserver


Management commands
-------------------

You can generate the CSS for Pygment's syntax highlighting:

    $ ./manage.py dumpstyles

Update the included highlight styles like this:

    $ ./manage.py dumpstyles > static/src/_highlight-styles.scss
