# lots of errors around punctuation in our import of NET bible
import re
from bibleverses.models import Verse


for v in Verse.objects.filter(version__slug='NET', text__regex=r"[A-Za-z][.,!?\"]+[A-Za-z]"):
    text = v.text

    # commas
    text = re.sub("([A-Za-z]),([A-Za-z])", "\\1, \\2", text)

    # a,"A
    text = re.sub("([A-Za-z]),\"([A-Za-z])", "\\1, \"\\2", text)

    # Others are ambiguous, fix by hand
    #text = re.sub("([A-Za-z])?\"([A-Za-z])", "\\1? \"\\2", text)
    #text = re.sub("([A-Za-z])?\"([A-Za-z])", "\\1? \"\\2", text)

    #text = text.replace(',"', ', "')
    #text = text.replace(',"', ', "')
    v.text = text
    v.save()

