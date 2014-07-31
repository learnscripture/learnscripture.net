from __future__ import unicode_literals

import pickle
from django.core.management.base import BaseCommand

import logging
logger = logging.getLogger(__name__)

def get_thesaurus(fname):
    f = file(fname).read().decode('utf8')
    return dict((l.split(',')[0], l.split(',')[1:]) for l in f.split('\r'))



# Thesaurus file tends to have unhelpful suggestions for pronouns, so we overwrite.
# These are not synonyms, but likely alternatives
OBJECTS = ['me', 'you', 'yourself', 'oneself', 'thee', 'him', 'her', 'himself', 'herself', 'it', 'itself', 'us', 'ourselves', 'yourselves', 'them', 'themselves']
SUBJECTS = ['i', 'you', 'thou', 'he', 'she', 'it', 'we', 'they']

PRONOUN_THESAURUS = dict(
    [(k, [v for v in OBJECTS if v != k]) for k in OBJECTS] +
    [(k, [v for v in SUBJECTS if v != k]) for k in SUBJECTS]
)

def version_thesaurus(version, base_thesaurus):
    fname = "../data/" + version.slug + ".thesaurus"
    try:
        return pickle.load(file(fname))
    except IOError:
        pass

    thesaurus = base_thesaurus.copy()
    thesaurus.update(PRONOUN_THESAURUS)

    from bibleverses.suggestions import get_all_version_words
    d = {}
    print "Building thesaurus for %s" % version.slug
    words = get_all_version_words(version.slug)
    for word, c in words.items():
        alts = thesaurus.get(word, None)
        if alts is None:
            d[word] = []
            continue

        # Don't allow multi-word alternatives
        alts = [a for a in alts if not ' ' in a]
        # Don't allow alternatives that don't appear in the text
        alts = [a for a in alts if a in words]
        # Normalise and exclude self
        alts = [a.lower() for a in alts if a != word]
        # Sort according to frequency in text
        alts_with_freq = [(words[a], a) for a in alts]
        alts_with_freq.sort(reverse=True)
        d[word] = [w for c,w in alts_with_freq]

    with file(fname, "w") as f:
        pickle.dump(d, f)
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

        for v in TextVersion.objects.all():
            print "=== " + v.slug + " ==="
            if thesaurus:
                v_thesaurus = version_thesaurus(v, thesaurus)
            else:
                v_thesaurus = None
            generate_suggestions(v, missing_only=True, thesaurus=v_thesaurus)
