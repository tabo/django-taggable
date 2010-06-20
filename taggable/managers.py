"Taggable managers"

from django.db import models
from taggable.querysets import TaggedQuerySet, EmptyTaggedQuerySet


class TaggedManager(models.Manager):
    "Manager for the Tagged abstract class. Subclass if needed."

    def _kwargs(self):
        "Returns **kwargs to be used by the get query set methods"
        try:
            # django 1.2+
            return {'using': self._db}
        except AttributeError:
            # django 1.1
            return {}

    def get_empty_query_set(self):
        return EmptyTaggedQuerySet(self.model, **self._kwargs())

    def get_query_set(self):
        return TaggedQuerySet(self.model, **self._kwargs())
