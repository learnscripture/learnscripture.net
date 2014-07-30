
from django.core.management.base import BaseCommand

import logging
logger = logging.getLogger(__name__)

def get_thesaurus(fname):
    f = file(fname).read()
    return dict((l.split(',')[0], l.split(',')[1:]) for l in f.split('\r'))


def version_thesaurus(version, base_thesaurus):
    from bibleverses.suggestions import get_all_version_words
    d = {}
    print "Building thesaurus for %s" % version.slug
    words = get_all_version_words(version.slug)
    for w in words:
        alts = base_thesaurus.get(w, None)
        if alts is None:
            d[w] = []
            continue

        # Don't allow multi-word alternatives
        alts = [a for a in alts if not ' ' in a]
        # Don't allow alternatives that don't appear in the text
        alts = [a for a in alts if a in words]
        # Normalise
        d[w] = [a.lower() for a in alts]
    return d

class Command(BaseCommand):
    def handle(self, *args, **options):
        # Pass filename of moby thesaurus .aur file as arg
        from bibleverses.suggestions import generate_suggestions
        from bibleverses.models import TextVersion

        if len(args) > 0:
            thesaurus = get_thesaurus(args[0])
        else:
            thesaurus = None
            print "WARNING: Generating without thesaurus"

        for v in TextVersion.objects.all()[0:1]:
            print "=== " + v.slug + " ==="
            if thesaurus:
                v_thesaurus = version_thesaurus(v, thesaurus)
            else:
                v_thesaurus = None
            generate_suggestions(v, missing_only=True, thesaurus=v_thesaurus)
