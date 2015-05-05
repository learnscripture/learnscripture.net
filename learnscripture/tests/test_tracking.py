from __future__ import absolute_import

from django.test import TestCase
from django.utils import timezone

from bibleverses.models import TextVersion, TextType
from tracking.models import TrackingSnapshot, auto_track_querysets, rewind_models


class TestTracking(TestCase):

    def test_insert(self):
        tv = TextVersion.objects.create(short_name='Fribble',
                                        slug='fribble',
                                        full_name='Fribble',
                                        text_type=TextType.BIBLE)
        tv.save()
        s = TrackingSnapshot.register_insert(tv)
        s.unapply()
        self.assertEqual(TextVersion.objects.filter(id=tv.id).count(),
                         0)
        s.apply()
        self.assertEqual(TextVersion.objects.filter(id=tv.id).count(),
                         1)

    def test_update(self):
        tv = TextVersion.objects.create(short_name='Fribble',
                                        slug='fribble',
                                        full_name='Fribble',
                                        text_type=TextType.BIBLE)

        tv1 = TextVersion.objects.get(id=tv.id)
        tv2 = TextVersion.objects.get(id=tv.id)
        tv2.full_name = "Altered"
        tv2.save()
        s = TrackingSnapshot.register_update(tv1, tv2)
        s.unapply()
        self.assertEqual(TextVersion.objects.get(id=tv.id).full_name,
                         'Fribble')
        s.apply()
        self.assertEqual(TextVersion.objects.get(id=tv.id).full_name,
                         'Altered')

    def test_delete(self):
        tv = TextVersion.objects.create(short_name='Fribble',
                                        slug='fribble',
                                        full_name='Fribble',
                                        text_type=TextType.BIBLE)
        tv.save()
        TextVersion.objects.filter(id=tv.id).delete()
        s = TrackingSnapshot.register_delete(tv)
        s.unapply()
        self.assertEqual(TextVersion.objects.filter(id=tv.id).count(),
                         1)
        s.apply()
        self.assertEqual(TextVersion.objects.filter(id=tv.id).count(),
                         0)

    def test_track_qs(self):
        qs = TextVersion.objects.all()
        t0 = timezone.now()
        with auto_track_querysets([qs]):
            tv = TextVersion.objects.create(short_name='Fribble',
                                            slug='fribble',
                                            full_name='1',
                                            text_type=TextType.BIBLE)

        t1 = timezone.now()
        with auto_track_querysets([qs]):
            tv.full_name = "2"
            tv.save()

        t2 = timezone.now()
        with auto_track_querysets([qs]):
            tv.full_name = "3"
            tv.save()

        t3 = timezone.now()
        with auto_track_querysets([qs]):
            TextVersion.objects.all().delete()

        # End.
        self.assertEqual(TextVersion.objects.filter(id=tv.id).count(),
                         0)
        # Now rewind
        rewind_models(TextVersion, t3)
        self.assertEqual(TextVersion.objects.get(id=tv.id).full_name,
                         "3")

        rewind_models(TextVersion, t2)
        self.assertEqual(TextVersion.objects.get(id=tv.id).full_name,
                         "2")

        rewind_models(TextVersion, t1)
        self.assertEqual(TextVersion.objects.get(id=tv.id).full_name,
                         "1")

        rewind_models(TextVersion, t0)
        self.assertEqual(TextVersion.objects.filter(id=tv.id).count(),
                         0)

        # Forward again, part way
        rewind_models(TextVersion, t2)
        self.assertEqual(TextVersion.objects.get(id=tv.id).full_name,
                         "2")
