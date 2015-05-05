#!/usr/bin/env python
from bibleverses.models import Verse

data = file('fix_net_2_data.txt').readlines()

for line in data:
    _, ref, rest = line.split(' ', 2)
    rest = rest.strip()
    ref = ref.strip(':')
    if rest.startswith('<hi type="italic">') and '</hi>' in rest:
        s = rest.index('>', 1)
        e = rest.index('</hi', s)
        title = rest[s + 1:e].strip()

        print
        print ref, title
        assert '<' not in title
        v = Verse.objects.get(version__slug='NET', reference='Psalm ' + ref)
        # Random fixes:
        v.text = v.text.replace('. "', '."')
        assert v.text.startswith(title)
        v.text = v.text[len(title):].strip()
        print v.text
        v.save()
