import os
os.environ['DJANGO_SETTINGS_MODULE'] = 'learnscripture.settings'

import django
django.setup()

from django.db import transaction
from django.db.models import F

import attr
from bibleverses.models import TextVersion, Verse
from bibleverses.parsing import parse_validated_localized_reference
from bibleverses.suggestions.modelapi import generate_suggestions

MISSING_VERSE_REFS = {
    'en': '3 John 1:15',
    'tr': '3. Yuhanna 1:15',
}


MISSING_VERSE_TEXTS = {
    'ESV': 'Peace be to you. The friends greet you. Greet the friends, each by name.',
    'NET': 'Peace be with you. The friends here greet you. Greet the friends there by name.'
}


def fix_missing_verse():
    fixed = []
    for version in TextVersion.objects.bibles():
        print(version.slug)
        ref = MISSING_VERSE_REFS[version.language_code]
        if Verse.objects.filter(version=version, localized_reference=ref).exists():
            # The verse is not missing in this version, everything is OK.
            continue

        parsed_ref = parse_validated_localized_reference(version.language_code, ref)
        # previous_ref:
        assert parsed_ref.start_verse > 1
        previous_ref = attr.evolve(parsed_ref,
                                   start_verse=parsed_ref.start_verse - 1,
                                   end_verse=parsed_ref.start_verse - 1,
                                   )
        previous_verse = Verse.objects.get(version=version,
                                           localized_reference=previous_ref.canonical_form())
        previous_non_missing_verse = (
            previous_verse if previous_verse.gapless_bible_verse_number is not None
            else Verse.objects.get(
                version=version,
                bible_verse_number__lt=previous_verse.bible_verse_number,
                gapless_bible_verse_number__isnull=False
            )
        )
        if version.slug in MISSING_VERSE_TEXTS:
            # The verse is missing in this version, wrongly.
            # We need to create the verse, shifting both
            # 'bible_verse_number' and 'gapless_bible_verse_number' down.
            text = MISSING_VERSE_TEXTS[version.slug]
            print(f'Creating verse: {text}')

            def shift():
                Verse.objects.filter(
                    version=version,
                    bible_verse_number__gt=previous_verse.bible_verse_number,
                ).update(
                    bible_verse_number=F('bible_verse_number') + 1,
                    gapless_bible_verse_number=F('gapless_bible_verse_number') + 1,
                )
        else:
            # The verse should be missing. We need to create a new
            # Verse object with missing=True. We have to shift
            # bible_verse_number down, but not gapless_bible_verse_number
            print(f'Creating empty verse')
            text = ''

            def shift():
                Verse.objects.filter(
                    version=version,
                    bible_verse_number__gt=previous_verse.bible_verse_number,
                ).update(
                    bible_verse_number=F('bible_verse_number') + 1,
                )

        with transaction.atomic():
            shift()
            missing = text == ''
            new_verse = Verse.objects.create(
                version=version,
                localized_reference=ref,
                text_saved=text,
                book_number=parsed_ref.book_number,
                chapter_number=parsed_ref.start_chapter,
                first_verse_number=parsed_ref.start_verse,
                last_verse_number=parsed_ref.end_verse,
                bible_verse_number=previous_verse.bible_verse_number + 1,
                gapless_bible_verse_number=(
                    None if missing else
                    previous_non_missing_verse.gapless_bible_verse_number + 1
                ),
                missing=missing,
                merged_into=previous_non_missing_verse if missing else None,
            )
            if version.language_code != 'tr':
                generate_suggestions(version, localized_reference=ref)
            fixed.append(new_verse)
            version.update_text_search(verse_id=new_verse.id)


if __name__ == '__main__':
    fix_missing_verse()
