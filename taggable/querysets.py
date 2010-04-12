"""

    taggable.querysets
    ------------------

    Django querysets.

    :copyright: 2010 by Gustavo Picon
    :license: Apache License 2.0

"""

from django.db import models


def _fieldname2model(queryset, fieldname):
    return queryset.model._meta.get_field_by_name(fieldname)[0].rel.to


def _queryset_filter_with_counts(qset, fieldname, qfilter, model, counts):
    if qfilter is not None:
        qset = qfilter(qset)
    for tagdata in qset:
        tag = model(**dict(
            [(t, tagdata['%s__%s' % (fieldname, t)]) for t in
             model.taggable_fields]))
        if counts:
            tag.count = tagdata['count']
        yield tag


class TaggedQuerySet(models.query.QuerySet):
    """ Queryset for the Tagged abstract class.
    """

    def delete(self):
        """ Removes a set of tagged objects and updates the stats tables.
        """

        for tagged in self:
            for fields, statsmodel in tagged.taggable_stats.items():
                qdict = dict(tagged.taggable_get_fields(fields))
                statsmodel.objects.filter(**qdict).filter(
                    count__lte=1).delete()
                statsmodel.objects.filter(**qdict).filter(
                    count__gte=2).update(count=models.F('count') - 1)

        super(TaggedQuerySet, self).delete()

    def get_tags(self, counts=False, qfilter=None):
        """ TODO: get_tags docstring
        """
        return self.get_tagged_fields(fieldname='tag',
                                      counts=counts,
                                      qfilter=qfilter)

    def get_tagged_fields(self, fieldname, counts=False, qfilter=None):
        """ TODO: get_tagged_fields docstring
        """
        model = _fieldname2model(self, fieldname)
        tagfields = ['%s__%s' % (fieldname, t) for t in
                     model.taggable_fields]
        qset = self.select_related(fieldname).values(*tagfields)
        if counts:
            qset = qset.annotate(count=models.Count('%s__id' % fieldname))
        else:
            qset = qset.distinct()
        return _queryset_filter_with_counts(qset, fieldname, qfilter,
                                            model, counts)

    def get_tagged_related(self, fieldname):
        """ TODO: get_tagged_related docstring
        """
        return _fieldname2model(self, fieldname).objects.filter(
            id__in=self.values('%s__id' % fieldname).distinct())


class EmptyTaggedQuerySet(models.query.EmptyQuerySet):

    def get_tags(self, counts=False, qfilter=None):
        return self.get_tagged_fields(fieldname='tag',
                                      counts=counts,
                                      qfilter=qfilter)

    def get_tagged_fields(self, fieldname, counts=False, qfilter=None):
        return _fieldname2model(self, fieldname).objects.none()

    def get_tagged_related(self, fieldname):
        return _fieldname2model(self, fieldname).objects.none()
