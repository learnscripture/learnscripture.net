import re
import urllib

from pyquery import PyQuery

ESV_BASE_URL = "http://www.esvapi.org/v2/rest/"

def get_esv(reference_list):
    from django.conf import settings

    params = ['key=%s' % settings.ESV_API_KEY,
              'passage=%s' % urllib.quote(";".join(reference_list)),
              'include-short-copyright=0',
              # Starting with plain text is easier than messing around
              # with massaging HTML, even if it means we have to parse
              # the output in a slightly adhoc way.
              'output-format=plain-text',
              'include-passage-horizontal-lines=0',
              'include-heading-horizontal-lines=0',
              'include-footnotes=0',
              'include-subheadings=0',
              'include-headings=0',
              'line-length=0',
              ]


    url = ESV_BASE_URL + "passageQuery?" + "&".join(params)
    page = urllib.urlopen(url)
    text = page.read()

    # Split into passages
    sections = {}
    current_section = None
    for line in text.split("\n"):
        if line.strip() == "":
            continue
        if line[0] != ' ' and line[0] != '[':
            current_section = line.strip()
        else:
            assert current_section is not None
            line = re.sub('\[[\d:]*\]', '', line).strip()
            prev = sections[current_section] + '\n' if current_section in sections else ''
            sections[current_section] = prev + line

    return sections

def search_esv(version, words):
    from django.conf import settings
    from bibleverses.models import ComboVerse

    params = ['key=%s' % settings.ESV_API_KEY,
              'words=%s' % words,
              'include-short-copyright=0',
              'include-passage-horizontal-lines=0',
              'include-heading-horizontal-lines=0',
              'include-footnotes=0',
              'include-subheadings=0',
              'include-headings=0',
              ]


    url = ESV_BASE_URL + "query?" + "&".join(params)
    page = urllib.urlopen(url)
    text = page.read()

    # Split into results
    refs = []
    pq = PyQuery(text)
    for elem in pq.find('p.search-result'):
        pq2 = PyQuery(elem)
        ref = pq2.find('.search-result-head a')[0].text_content()
        refs.append(ref)

    # It's easier at this point to get the verse via 'get_esv'
    verses = version.get_verses_by_reference_bulk(refs)
    return [ComboVerse(ref, [verses[ref]]) for ref in refs]
