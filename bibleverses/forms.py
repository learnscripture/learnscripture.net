from django import forms

from bibleverses.models import BIBLE_BOOKS


class VerseSelector(forms.Form):
    book = forms.ChoiceField(choices=[(b,b) for b in BIBLE_BOOKS])
    chapter = forms.IntegerField()
    start_verse = forms.IntegerField(required=False)
    end_verse = forms.IntegerField(required=False)
