Captain Pasty
=============

A pastebin on Google App Engine's Python runtime. It looks a bit like GitHub's Gist.


Installation
------------

You must install the App Engine SDK yourself. Then install Captain Pasty and its dependencies.

    $ git clone https://github.com/davidwtbuxton/captain-pasty.git
    $ cd captain-pasty
    $ ./installdeps.sh

Run the development server:

    $ python manage.py runserver


Configuration
-------------

Captain Pasty will use the default Cloud Storage bucket, but you can override that by naming a different bucket in Django settings:

    # Add this to your project's settings.py
    CLOUD_STORAGE_BUCKET = 'my-custom-bucket-name'
