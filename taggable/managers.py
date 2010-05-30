"Taggable managers"

from django.db import models
from taggable.querysets import TaggedQuerySet, EmptyTaggedQuerySet


class TaggedManager(models.Manager):
    """ Manager for the Tagged abstract class.
    """

    def _kwargs(self):
        try:
            # django 1.2+
            return {'using': self._db}
        except AttributeError:
            # django 1.1
            return {}

    def get_empty_query_set(self):
        """ TODO: docstring
        """
        return EmptyTaggedQuerySet(self.model, **self._kwargs())

    def get_query_set(self):
        """ TODO: docstring
        """
        return TaggedQuerySet(self.model, **self._kwargs())
