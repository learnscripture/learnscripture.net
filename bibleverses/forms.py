from django import forms

from bibleverses.models import BIBLE_BOOKS, VerseSet


class VerseSelector(forms.Form):
    book = forms.ChoiceField(choices=[(b,b) for b in BIBLE_BOOKS])
    chapter = forms.IntegerField()
    start_verse = forms.IntegerField(required=False)
    end_verse = forms.IntegerField(label=u"End verse (optional)", required=False)

    def make_reference(self):
        """
        Returns reference from cleaned_data, assuming forms validates.
        """
        reference = u"%s %s" % (self.cleaned_data['book'],
                                self.cleaned_data['chapter'])
        start_verse = self.cleaned_data['start_verse']
        if start_verse is not None:
            reference = u"%s:%s" % (reference, start_verse)
            end_verse = self.cleaned_data['end_verse']
            if end_verse is not None:
                reference =  u"%s-%s" % (reference, end_verse)
        return reference


class VerseSetForm(forms.ModelForm):
    class Meta:
        model = VerseSet
        fields = ('name', 'description')

a = VerseSetForm.base_fields['description'].widget.attrs
del a['cols']
a['rows'] = 3
