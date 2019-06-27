# Generated by Django 2.0.10 on 2019-06-22 11:42

from django.db import migrations


def forwards(apps, schema_editor):
    FiberContentItem = apps.get_model('fiber', 'ContentItem')
    FiberPage = apps.get_model('fiber', 'Page')
    FiberPageContentItem = apps.get_model('fiber', 'PageContentItem')
    FiberFile = apps.get_model('fiber', 'File')
    FiberImage = apps.get_model('fiber', 'Image')

    ContentItem = apps.get_model('cms', 'ContentItem')
    Page = apps.get_model('cms', 'Page')
    PageContentItem = apps.get_model('cms', 'PageContentItem')
    File = apps.get_model('cms', 'File')
    Image = apps.get_model('cms', 'Image')

    page_map = {}
    content_item_map = {}
    # Ordering this way means we can create dependencies first,
    # it happens that we don't have any cyclic issues so this is enough.
    for p in FiberPage.objects.order_by('-parent', '-redirect_page'):
        new_p = Page()
        new_p.__dict__.update(p.__dict__)
        new_p.id = None
        new_p.redirect_page = page_map.get(p.redirect_page, None)
        new_p.parent = page_map.get(p.parent, None)
        new_p.save()
        page_map[p] = new_p

    for c in FiberContentItem.objects.all():
        new_c = ContentItem()
        new_c.__dict__.update(c.__dict__)
        new_c.id = None
        new_c.save()
        content_item_map[c] = new_c

    for pc in FiberPageContentItem.objects.all():
        new_pc = PageContentItem()
        new_pc.__dict__.update(pc.__dict__)
        new_pc.id = None
        new_pc.content_item = content_item_map[pc.content_item]
        new_pc.page = page_map[pc.page]
        new_pc.save()

    for f in FiberFile.objects.all():
        new_f = File()
        new_f.__dict__.update(f.__dict__)
        new_f.id = None
        new_f.save()

    for i in FiberImage.objects.all():
        new_i = Image()
        new_i.__dict__.update(i.__dict__)
        new_i.id = None
        new_i.save()


def backwards(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('cms', '0001_initial'),
        ('fiber', '0002_callable_upload_to'),
    ]

    operations = [
        migrations.RunPython(forwards, backwards),
    ]
