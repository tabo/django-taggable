django-taggable
===============

`django-taggable <https://tabo.pe/projects/django-taggable/>`_
is a library that implements a efficient tagging implementations for the
`Django Web Framework 1.1+ <http://www.djangoproject.com/>`_, written by
`Gustavo Picón <https://tabo.pe>`_ and licensed under the Apache License 2.0.

``django-taggable`` is:

- **Flexible**: Uses `tagtools <https://tabo.pe/projects/tagtools/>`_ to
  choose between popular tagging styles
  (`flickr <https://tabo.pe/projects/tagtools/docs/tip/flickr.html>`_,
  `delicious <https://tabo.pe/projects/tagtools/docs/tip/delicious.html>`_,
  `etc <https://tabo.pe/projects/tagtools/docs/tip/comma.html>`_), or
  define your own. You can also easily have several tag fields per object or
  have different tag "namespaces" to be used between one, some or all your
  taggable objects. Your code, your choice.
- **Sane**: No GenericForeignKey madness.
- **Easy**: Uses `Django Model Inheritance with abstract classes`_
  to define your own models. The API isn't "magical".
- **Clean**: Testable and well tested code base. Code/branch test coverage
  is 100%.

Contents
--------

.. toctree::
   :maxdepth: 2

   api


.. _`Django Model Inheritance with abstract classes`:
   http://docs.djangoproject.com/en/dev/topics/db/models/#abstract-base-classes


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

