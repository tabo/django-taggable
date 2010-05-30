"Taggable signals"

from django.db import models, transaction


def _handler_obj_delete(signal, sender, instance, **named):
    """ Removes all related tagged stats objects

    Called when a tagged/tag object is delete()d

    """
    try:
        # we assume that if we have a this property, we're fine
        instance.taggable_on_delete
    except AttributeError:
        # this is not an object associated to a Tagged model
        return
    for field_name, tagged_model in instance.taggable_on_delete:
        where = ['%s=%s' % (
                 tagged_model._meta.get_field_by_name(field_name)[0].column,
                 instance.pk)]
        tagged_model.objects.extra(where=where).delete()
    transaction.commit_unless_managed()


def _handler_tagged_subclass(signal, sender, **named):
    """ Handler for the class_prepared signal.
    """
    from taggable.models import Tagged

    if not issubclass(sender, Tagged):
        # we only want Tagged subclasses
        return

    # we start caching the stats fields
    try:
        stats = sender.Taggable.stats
    except AttributeError:
        stats = {}

    sender.taggable_sorted_stats = [
        (tuple(sorted(k)), v) for (k, v) in stats.items()]
    sender.taggable_sorted_stats.sort(key=lambda x: len(x[0]), reverse=True)
    sender.taggable_stats = dict(sender.taggable_sorted_stats)

    sender.taggable_taggedfields = set()
    sender.taggable_taggedfields_notag = set()

    for field, _ in sender._meta.get_fields_with_model():
        if field.get_internal_type() != 'ForeignKey':
            continue
        rel_model = field.rel.to

        try:
            rel_model.taggable_on_delete
        except AttributeError:
            rel_model.taggable_on_delete = set()
        for stats_fields, _ in sender.taggable_stats.items():
            if field.name not in stats_fields:
                rel_model.taggable_on_delete.add((field.name, sender))

        if field.name != 'tag':
            sender.taggable_taggedfields_notag.add(field.name)
        sender.taggable_taggedfields.add(field.name)

        rel_model.taggable_fields = set()
        for rfield, _ in rel_model._meta.get_fields_with_model():
            rel_model.taggable_fields.add(rfield.name)


def register():
    """Internal function to register all known signals
    """
    models.signals.class_prepared.connect(_handler_tagged_subclass)
    models.signals.pre_delete.connect(_handler_obj_delete)
