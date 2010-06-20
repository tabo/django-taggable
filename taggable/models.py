"Taggable models"

from django.db import models
from taggable.managers import TaggedManager
from taggable.querysets import queryset_filter_with_counts
from taggable.exceptions import InvalidFields


class Tagged(models.Model):
    objects = TaggedManager()

    def taggable_get_fields(self, fields):
        results = []
        for field in fields:
            val = self.__getattribute__(field)
            results.append((field, val))
        return results

    def save(self, *args, **kwargs):
        "Saves the tagged object and handles the stats table maintenance."
        super(Tagged, self).save(*args, **kwargs)

        for fields, statsmodel in self.taggable_stats.items():
            qdict = dict(self.taggable_get_fields(fields))
            qset = statsmodel.objects.filter(**qdict)
            updated_rows = qset.update(count=models.F('count') + 1)
            if updated_rows == 0:
                # 0 rows updated, this means we need to create a stats entry
                qdict['count'] = 1
                statsmodel(**qdict).save(force_insert=True)

    @classmethod
    def tag_count(cls, **fields):
        key = tuple(sorted(fields.keys()))
        if key in cls.taggable_stats:
            model = cls.taggable_stats[key]
            try:
                return model.objects.get(**fields).count
            except model.DoesNotExist:
                return 0
        return cls.objects.filter(**fields).count()

    @classmethod
    def _check_fields(cls, allfields=False, includetag=False, **fields):
        keys_set = set(fields.keys())
        if includetag:
            tagged_fields = cls.taggable_taggedfields
        else:
            tagged_fields = cls.taggable_taggedfields_notag
        if allfields:
            if keys_set ^ tagged_fields:
                raise InvalidFields
        else:
            if keys_set - tagged_fields:
                raise InvalidFields

    @classmethod
    def add_tag(cls, tag, **fields):
        cls._check_fields(allfields=True, includetag=False, **fields)
        fields['tag'] = tag
        try:
            return cls.objects.get(**fields)
        except cls.DoesNotExist:
            obj = cls(**fields)
            obj.save()
            return obj

    @classmethod
    def update_tags(cls, tags, **fields):
        cls._check_fields(allfields=True, includetag=False, **fields)
        if not tags:
            tags = []
        # remove old tags
        cls.objects.filter(**fields).exclude(tag__in=tags).delete()
        # set new tags
        return [cls.add_tag(tag, **fields) for tag in tags]

    @classmethod
    def get_tags(cls, counts=False, qfilter=None, **fields):
        return cls.get_tagged_fields(fieldname='tag',
                                     counts=counts,
                                     qfilter=qfilter,
                                     **fields)

    @classmethod
    def get_tagged_fields(cls, fieldname, counts=False, qfilter=None,
                          **fields):
        cls._check_fields(allfields=False, includetag=True, **fields)
        if cls.taggable_sorted_stats:
            model = cls._meta.get_field_by_name(fieldname)[0].rel.to
            tagfields = ['%s__%s' % (fieldname, t) for t in
                         model.taggable_fields]
            fields_keys_set = set(fields.keys() + [fieldname])
            for keys, statsmodel in cls.taggable_sorted_stats:
                if set(keys) ^ fields_keys_set:
                    continue
                # we found a usable stats table for this query
                qset = statsmodel.objects.select_related(
                    fieldname).filter(**fields)
                if counts:
                    qset = qset.values(*tagfields + ['count'])
                else:
                    qset = qset.values(*tagfields).distinct()
                return queryset_filter_with_counts(qset, fieldname,
                                                    qfilter, model, counts)
        # no usable stats table
        # we fall back to queryset.get_tagged_fields()
        return cls.objects.filter(**fields).get_tagged_fields(fieldname,
            counts=counts, qfilter=qfilter)

    class Meta:
        "Abstract model."
        abstract = True

    class Taggable:
        pass
