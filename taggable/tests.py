"Taggable unit/functional tests"

import functools

from django.test import TestCase
from django.db import models, transaction
from taggable.models import Tagged
from taggable.exceptions import InvalidFields


class Monster(models.Model):
    name = models.CharField(max_length=100)

    def __unicode__(self):  # pragma: no cover
        return self.name


class User(models.Model):
    name = models.CharField(max_length=100)

    def __unicode__(self):  # pragma: no cover
        return self.name


class Category(models.Model):
    name = models.CharField(max_length=100)

    def __unicode__(self):  # pragma: no cover
        return self.name


class Tag(models.Model):
    name = models.CharField(max_length=100)

    def __unicode__(self):  # pragma: no cover
        return self.name


class SimpleStats(models.Model):
    tag = models.ForeignKey(Tag, primary_key=True)
    count = models.PositiveIntegerField(default=0)


class SimpleTagged(Tagged):
    tag = models.ForeignKey(Tag)
    monster = models.ForeignKey(Monster)

    def __unicode__(self):  # pragma: no cover
        return '%s %s' % (self.tag, self.monster)

    class Meta:
        unique_together = (('tag', 'monster'), )

    class Taggable:
        stats = {
            ('tag', ): SimpleStats,
        }


class SimpleTaggedNoStats(Tagged):
    tag = models.ForeignKey(Tag)
    monster = models.ForeignKey(Monster)

    def __unicode__(self):  # pragma: no cover
        return '%s %s' % (self.tag, self.monster)

    class Meta:
        unique_together = (('tag', 'monster'), )


class StatsTag(models.Model):
    tag = models.ForeignKey(Tag, unique=True)
    count = models.PositiveIntegerField(default=0)


class StatsTagUsr(models.Model):
    tag = models.ForeignKey(Tag)
    user = models.ForeignKey(User)
    count = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = (('tag', 'user'), )


class StatsTagUsrCat(models.Model):
    tag = models.ForeignKey(Tag)
    user = models.ForeignKey(User)
    category = models.ForeignKey(Category)
    count = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = (('tag', 'user', 'category'), )


class ComplexTagged(Tagged):
    tag = models.ForeignKey(Tag)
    user = models.ForeignKey(User)
    category = models.ForeignKey(Category)
    monster = models.ForeignKey(Monster)

    def __unicode__(self):  # pragma: no cover
        return '%s %s %s %s' % (self.tag, self.monster, self.user,
                                self.category)

    class Meta:
        unique_together = (('tag', 'user', 'category', 'monster'), )

    class Taggable:
        stats = {
            ('tag', ): StatsTag,
            ('tag', 'user'): StatsTagUsr,
            ('tag', 'user', 'category'): StatsTagUsrCat,
        }


class ComplexTaggedNoStats(Tagged):
    tag = models.ForeignKey(Tag)
    user = models.ForeignKey(User)
    category = models.ForeignKey(Category)
    monster = models.ForeignKey(Monster)

    def __unicode__(self):  # pragma: no cover
        return '%s %s %s %s' % (self.tag, self.monster, self.user,
                                self.category)

    class Meta:
        unique_together = (('tag', 'user', 'category', 'monster'), )


def testtype(tagtype='simple', stats=False):

    def decorator(f):

        @functools.wraps(f)
        def _testtype(self):
            self.taggedmodel = {
                ('simple', True): SimpleTagged,
                ('simple', False): SimpleTaggedNoStats,
                ('complex', True): ComplexTagged,
                ('complex', False): ComplexTaggedNoStats}[(tagtype, stats)]
            try:
                f(self)
            finally:
                transaction.rollback()
                self.taggedmodel = None
        return _testtype
    return decorator


def _load_test_methods(cls):
    for m in dir(cls):
        is_simple = 'simple' in m
        if not m.startswith('_simple_') and not m.startswith('_complex_'):
            continue
        for stats in (False, True):
            deco = testtype('simple' if is_simple else 'complex', stats)
            name = 'test_%s%s' % ('stats' if stats else 'nostats', m)
            setattr(cls, name, deco(getattr(cls, m)))


class TestBase(TestCase):

    def setUp(self):
        self.taggedmodel = None
        super(TestBase, self).setUp()

    def cplxtest(self, user, category, tag, expected):
        l, tm = expected, self.taggedmodel
        self.assertEqual(l[0], tm.tag_count())
        self.assertEqual(l[1], tm.tag_count(user=user))
        self.assertEqual(l[2], tm.tag_count(category=category))
        self.assertEqual(l[3], tm.tag_count(user=user, category=category))
        self.assertEqual(l[4], tm.tag_count(tag=tag))
        self.assertEqual(l[5], tm.tag_count(tag=tag, user=user))
        self.assertEqual(l[6], tm.tag_count(tag=tag, category=category))
        self.assertEqual(l[7], tm.tag_count(tag=tag, user=user,
                                        category=category))

    def get_tags_helper(self, tested, expected, partial_tresh, empty_tresh,
                        **kwargs):
        self.assertEqual(expected,
            [(t.name, t.count) for t in
             tested.get_tags(counts=True,
                             qfilter=lambda q: q.order_by('tag__name'),
                             **kwargs)])
        self.assertEqual([t for t in expected if t[1] >= partial_tresh],
            [(t.name, t.count) for t in
             tested.get_tags(counts=True,
                 qfilter=lambda q:
                     q.order_by('tag__name').filter(count__gte=partial_tresh),
                 **kwargs)])
        self.assertEqual([],
            [(t.name, t.count) for t in
             tested.get_tags(counts=True,
                 qfilter=lambda q:
                     q.order_by('tag__name').filter(count__gte=empty_tresh),
                 **kwargs)])
        self.assertEqual([t[0] for t in expected],
            sorted([t.name for t in tested.get_tags(**kwargs)]))
        self.assertEqual([t[0] for t in expected],
            [t.name for t in
             tested.get_tags(qfilter=lambda q: q.order_by('tag__name'),
                             **kwargs)])

        # now sorted the expected values by [-count, +tag__name]
        expected.sort(cmp=lambda x, y:
                                 y[1] - x[1]
                              if y[1] != x[1]
                            else x[0] > y[0])
        self.assertEqual(expected,
            [(t.name, t.count) for t in
             tested.get_tags(counts=True,
                             qfilter=lambda q: q.order_by('-count',
                                                         'tag__name'),
                             **kwargs)])
        self.assertEqual([t for t in expected if t[1] >= partial_tresh],
            [(t.name, t.count) for t in
             tested.get_tags(counts=True,
                 qfilter=lambda q:
                     q.order_by('-count', 'tag__name').filter(
                     count__gte=partial_tresh),
                 **kwargs)])
        self.assertEqual([],
            [(t.name, t.count) for t in
             tested.get_tags(counts=True,
                 qfilter=lambda q:
                     q.order_by('-count', 'tag__name').filter(
                     count__gte=empty_tresh),
                 **kwargs)])


class TestEmpty(TestBase):

    fixtures = ['test_objs.json']

    def _simple_empty_create_tag(self):
        monster = Monster.objects.get(name='Imp')

        tag = Tag(name='testtag')
        tag.save()

        self.assertEqual(0, self.taggedmodel.tag_count(tag=tag))
        self.taggedmodel.add_tag(tag, monster=monster)
        self.assertEqual(1, self.taggedmodel.tag_count(tag=tag))

    def _complex_empty_create_tag(self):
        monster = Monster.objects.get(name='Imp')
        user = User.objects.get(name='tabo')
        category = Category.objects.get(name='Devil')

        tag = Tag(name='testtag')
        tag.save()

        self.cplxtest(user, category, tag,
            (0, 0, 0, 0, 0, 0, 0, 0))
        self.taggedmodel.add_tag(tag, monster=monster, user=user,
            category=category)
        self.cplxtest(user, category, tag,
            (1, 1, 1, 1, 1, 1, 1, 1))


class TestSimple(TestBase):
    fixtures = ['test_objs.json', 'test_tags.json', 'test_simple.json']

    def _simple_delete_single(self):
        tag = Tag.objects.get(name='elemental')
        self.assertEqual(3, self.taggedmodel.tag_count(tag=tag))
        Monster.objects.get(name='Vrock').delete()
        self.assertEqual(2, self.taggedmodel.tag_count(tag=tag))

    def _simple_delete_multi(self):
        tag = Tag.objects.get(name='elemental')
        self.assertEqual(3, self.taggedmodel.tag_count(tag=tag))
        Monster.objects.filter(name__in=('Vrock', 'Balor')).delete()
        self.assertEqual(1, self.taggedmodel.tag_count(tag=tag))

    def _simple_model_get_tags_one(self):
        monster = Monster.objects.get(name='Zombie')
        expected = [(u'animate', 1), (u'brute', 1), (u'lvl2', 1),
                    (u'medium', 1), (u'natural', 1), (u'undead', 1)]
        self.get_tags_helper(self.taggedmodel, expected, 1, 2,
                             monster=monster)

    def _simple_model_get_tags_all(self):
        expected = [(u'animate', 1), (u'brute', 3), (u'demon', 3),
                    (u'devil', 1), (u'elemental', 3), (u'elite', 1),
                    (u'huge', 1), (u'humanoid', 4), (u'immortal', 1),
                    (u'large', 2), (u'lurker', 1), (u'lvl13', 1),
                    (u'lvl2', 1), (u'lvl22', 1), (u'lvl27', 1),
                    (u'lvl3', 1), (u'medium', 1), (u'natural', 1),
                    (u'skirmisher', 1), (u'tiny', 1), (u'undead', 1)]
        self.get_tags_helper(self.taggedmodel, expected, 3, 5)

    def _simple_model_get_tags_invalid(self):
        try:
            list(self.taggedmodel.get_tags(invalid=True))
        except InvalidFields:
            pass

    def _simple_queryset_get_tags_some(self):
        expected = [(u'animate', 1), (u'brute', 2), (u'demon', 1),
                    (u'elemental', 1), (u'humanoid', 1), (u'large', 1),
                    (u'lvl2', 1), (u'lvl22', 1), (u'medium', 1),
                    (u'natural', 1), (u'undead', 1)]
        qset = self.taggedmodel.objects.filter(monster__name__icontains='z')
        self.get_tags_helper(qset, expected, 2, 3)

    def _simple_queryset_get_tags_none(self):
        self.assertEqual(0,
            len(self.taggedmodel.objects.none().get_tags()))
        self.assertEqual(0,
            len(self.taggedmodel.objects.none().get_tags(counts=True)))

    def _simple_queryset_get_tags_all(self):
        expected = [(u'animate', 1), (u'brute', 3), (u'demon', 3),
                    (u'devil', 1), (u'elemental', 3), (u'elite', 1),
                    (u'huge', 1), (u'humanoid', 4), (u'immortal', 1),
                    (u'large', 2), (u'lurker', 1), (u'lvl13', 1),
                    (u'lvl2', 1), (u'lvl22', 1), (u'lvl27', 1),
                    (u'lvl3', 1), (u'medium', 1), (u'natural', 1),
                    (u'skirmisher', 1), (u'tiny', 1), (u'undead', 1)]
        self.get_tags_helper(self.taggedmodel.objects.all(), expected, 3, 5)

    def _simple_add_tag(self):
        monster = Monster.objects.get(name='Vrock')
        tag = Tag.objects.get(name='devil')

        self.assertEqual(1, self.taggedmodel.tag_count(tag=tag))
        # tagging several time just works
        for _ in range(3):
            self.taggedmodel.add_tag(tag, monster=monster)
            self.assertEqual(2, self.taggedmodel.tag_count(tag=tag))

    def _simple_add_tag_invalid(self):
        tag = Tag.objects.get(name='devil')
        self.assertRaises(InvalidFields, self.taggedmodel.add_tag,
                          tag, invalid=True)

    def _simple_update_tags_empty(self):
        # testing different ways of clearing the tags
        vals = [('Zombie', None),
                ('Vrock', []),
                ('Balor', Tag.objects.none())]
        for monster_name, updateval in vals:
            monster = Monster.objects.get(name=monster_name)
            self.taggedmodel.update_tags(updateval, monster=monster)
            self.assertEqual(0,
                self.taggedmodel.tag_count(monster=monster))

    def _simple_update_tags_replace_all(self):
        monster = Monster.objects.get(name='Zombie')
        tagnames = ['immortal', 'lvl27', 'tiny']
        newtags = Tag.objects.filter(name__in=tagnames)
        self.taggedmodel.update_tags(newtags, monster=monster)
        self.assertEqual(tagnames,
            [tag.name for tag in
             self.taggedmodel.objects.filter(
             monster=monster).get_tags(
                 qfilter=lambda q: q.order_by('tag__name'))])

    def _simple_update_tags_replace_some(self):
        monster = Monster.objects.get(name='Zombie')
        tagnames = ['animate', 'brute', 'immortal', 'lvl27', 'undead']
        newtags = Tag.objects.filter(name__in=tagnames)
        self.taggedmodel.update_tags(newtags, monster=monster)
        self.assertEqual(tagnames,
            [tag.name for tag in
             self.taggedmodel.objects.filter(
             monster=monster).get_tags(
             qfilter=lambda q: q.order_by('tag__name'))])

    def _simple_update_tags_invalid(self):
        tags = Tag.objects.filter(name='devil')
        self.assertRaises(InvalidFields, self.taggedmodel.update_tags,
                          tags, invalid=True)

    def _simple_get_tagged_related(self):
        expected = [u'Zombie', u'Hezrou']
        qset = self.taggedmodel.objects.filter(monster__name__icontains='z')
        self.assertEqual(expected,
            list(qset.get_tagged_related('monster').order_by(
                 '-name').values_list('name', flat=True)))

        self.assertEqual(0,
            self.taggedmodel.objects.none().get_tagged_related(
                'monster').count())

        self.assertRaises(models.fields.FieldDoesNotExist,
                          qset.get_tagged_related, 'INVALID_FIELD')


class TestComplex(TestBase):
    fixtures = ['test_objs.json', 'test_tags.json', 'test_complex.json']

    def setUp(self):
        super(TestComplex, self).setUp()
        self.user = User.objects.get(name='tabo')
        self.category = Category.objects.get(name='Demon')
        self.tag = Tag.objects.get(name='humanoid')

    def _complex_initial_data(self):
        self.cplxtest(self.user, self.category, self.tag,
            (50, 31, 24, 19, 5, 4, 3, 3))

    def _complex_delete_single(self):
        Monster.objects.get(name='Vrock').delete()
        self.cplxtest(self.user, self.category, self.tag,
            (41, 25, 18, 13, 3, 3, 2, 2))

    def _complex_delete_multi(self):
        Monster.objects.filter(name__in=('Vrock', 'Balor')).delete()
        self.cplxtest(self.user, self.category, self.tag,
            (26, 18, 8, 6, 2, 2, 1, 1))

    def _complex_model_get_tags_one_dimension(self):
        monster = Monster.objects.get(name='Zombie')
        expected = [(u'animate', 1), (u'brute', 2), (u'immortal', 1),
                    (u'lvl2', 1), (u'lvl22', 1), (u'medium', 1),
                    (u'natural', 1), (u'undead', 2)]
        self.get_tags_helper(self.taggedmodel, expected, 2, 3,
                             monster=monster)

    def _complex_model_get_tags_two_dimensions(self):
        expected = [(u'brute', 2), (u'demon', 3), (u'elemental', 3),
                    (u'elite', 1), (u'huge', 1), (u'humanoid', 3),
                    (u'large', 2), (u'lvl13', 1), (u'lvl22', 1),
                    (u'lvl27', 1), (u'skirmisher', 1)]
        self.get_tags_helper(self.taggedmodel, expected, 2, 4,
                             user=self.user, category=self.category)

        category = Category.objects.get(name='Devil')
        monster = Monster.objects.get(name='Imp')
        expected = [(u'devil', 1), (u'humanoid', 1), (u'immortal', 2),
                    (u'lurker', 1), (u'lvl3', 1), (u'tiny', 1)]
        self.get_tags_helper(self.taggedmodel, expected, 2, 3,
                             category=category, monster=monster)

    def _complex_model_get_tags_all(self):
        expected = [(u'animate', 2), (u'brute', 5), (u'demon', 3),
                    (u'devil', 2), (u'elemental', 3), (u'elite', 1),
                    (u'huge', 1), (u'humanoid', 5), (u'immortal', 4),
                    (u'large', 5), (u'lurker', 1), (u'lvl13', 1),
                    (u'lvl2', 2), (u'lvl22', 2), (u'lvl27', 2),
                    (u'lvl3', 1), (u'medium', 2), (u'natural', 1),
                    (u'skirmisher', 2), (u'tiny', 2), (u'undead', 3)]
        self.get_tags_helper(self.taggedmodel, expected, 4, 6)

    def _complex_model_get_tags_invalid(self):
        try:
            list(self.taggedmodel.get_tags(invalid=True))
        except InvalidFields:
            pass

    def _complex_queryset_get_tags_some(self):
        expected = [(u'animate', 1), (u'brute', 3), (u'demon', 1),
                    (u'elemental', 1), (u'humanoid', 1), (u'immortal', 1),
                    (u'large', 1), (u'lvl2', 1), (u'lvl22', 2),
                    (u'medium', 1), (u'natural', 1), (u'undead', 2)]
        qset = self.taggedmodel.objects.filter(monster__name__icontains='z',
                                               user__name__icontains='a')
        self.get_tags_helper(qset, expected, 2, 4)

    def _complex_queryset_get_tags_none(self):
        self.assertEqual(0,
            len(self.taggedmodel.objects.none().get_tags()))
        self.assertEqual(0,
            len(self.taggedmodel.objects.none().get_tags(counts=True)))

    def _complex_queryset_get_tags_all(self):
        expected = [(u'animate', 2), (u'brute', 5), (u'demon', 3),
                    (u'devil', 2), (u'elemental', 3), (u'elite', 1),
                    (u'huge', 1), (u'humanoid', 5), (u'immortal', 4),
                    (u'large', 5), (u'lurker', 1), (u'lvl13', 1),
                    (u'lvl2', 2), (u'lvl22', 2), (u'lvl27', 2),
                    (u'lvl3', 1), (u'medium', 2), (u'natural', 1),
                    (u'skirmisher', 2), (u'tiny', 2), (u'undead', 3)]
        self.get_tags_helper(self.taggedmodel.objects.all(), expected, 3, 6)

    def _complex_add_tag_invalid(self):
        tag = Tag.objects.get(name='devil')
        self.assertRaises(InvalidFields, self.taggedmodel.add_tag,
                          tag, invalid=True)

    def _complex_add_tag(self):
        monster = Monster.objects.get(name='Vrock')
        tag = Tag.objects.get(name='devil')

        self.assertEqual(2, self.taggedmodel.tag_count(tag=tag))

        # tagging several time just works
        for _ in range(3):
            self.taggedmodel.add_tag(tag, monster=monster, user=self.user,
                category=self.category)
            self.assertEqual(3, self.taggedmodel.tag_count(tag=tag))

    def _complex_update_tags_empty(self):
        # testing different ways of clearing the tags
        vals = [('Balor', None),
                ('Hezrou', []),
                ('Vrock', Tag.objects.none())]
        for monster_name, updateval in vals:
            monster = Monster.objects.get(name=monster_name)
            self.taggedmodel.update_tags(updateval, monster=monster,
                user=self.user, category=self.category)
            self.assertEqual(0,
                self.taggedmodel.tag_count(monster=monster,
                                           user=self.user,
                                           category=self.category))

    def _complex_update_tags_replace_all(self):
        monster = Monster.objects.get(name='Balor')
        tagnames = ['immortal', 'lvl2', 'tiny']
        newtags = Tag.objects.filter(name__in=tagnames)
        self.taggedmodel.update_tags(newtags, monster=monster,
            user=self.user, category=self.category)
        self.assertEqual(tagnames,
            [tag.name for tag in
                 self.taggedmodel.objects.filter(monster=monster,
                 user=self.user,
                 category=self.category).get_tags(
                 qfilter=lambda q: q.order_by('tag__name'))])

    def _complex_update_tags_replace_some(self):
        monster = Monster.objects.get(name='Balor')
        tagnames = ['brute', 'demon', 'immortal', 'lvl2']
        newtags = Tag.objects.filter(name__in=tagnames)
        self.taggedmodel.update_tags(newtags, monster=monster,
            user=self.user, category=self.category)
        self.assertEqual(tagnames,
            [tag.name for tag in
                 self.taggedmodel.objects.filter(monster=monster,
                 user=self.user,
                 category=self.category).get_tags(
                 qfilter=lambda q: q.order_by('tag__name'))])

    def _complex_update_tags_invalid(self):
        tags = Tag.objects.filter(name='devil')
        self.assertRaises(InvalidFields, self.taggedmodel.update_tags,
                          tags, invalid=True)

    def _complex_get_tagged_related(self):
        qset = self.taggedmodel.objects.filter(monster__name__icontains='z',
                                               user__name__icontains='a')
        self.assertEqual([u'Zombie', u'Hezrou'],
            list(qset.get_tagged_related('monster').order_by(
                 '-name').values_list('name', flat=True)))
        self.assertEqual([u'tabo', u'Alex'],
            list(qset.get_tagged_related('user').order_by(
                 '-name').values_list('name', flat=True)))
        expected = [u'undead', u'natural', u'medium', u'lvl22', u'lvl2',
                    u'large', u'immortal', u'humanoid', u'elemental',
                    u'demon', u'brute', u'animate']
        self.assertEqual(expected,
            list(qset.get_tagged_related('tag').order_by(
                 '-name').values_list('name', flat=True)))

        self.assertEqual(0,
            self.taggedmodel.objects.none().get_tagged_related(
                'monster').count())

        self.assertRaises(models.fields.FieldDoesNotExist,
                          qset.get_tagged_related, 'INVALID_FIELD')


_load_test_methods(TestEmpty)
_load_test_methods(TestSimple)
_load_test_methods(TestComplex)
