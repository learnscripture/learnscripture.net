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


class PassageVerseSelector(forms.Form):
    book = forms.ChoiceField(choices=[(b,b) for b in BIBLE_BOOKS])
    start_chapter = forms.IntegerField()
    start_verse = forms.IntegerField(label="Start verse (optional)", required=False)
    end_chapter = forms.IntegerField(label=u"End chapter (optional)", required=False)
    end_verse = forms.IntegerField(label=u"End verse (optional)", required=False)

    def clean(self):
         cleaned_data = super(PassageVerseSelector, self).clean()
         if (cleaned_data['end_chapter'] is not None and
             cleaned_data['end_verse'] is None):
             raise forms.ValidationError("'End verse' must be supplied if 'End chapter' is specified.")
         if (cleaned_data['end_verse'] is not None and
             cleaned_data['start_verse'] is None):
             raise forms.ValidationError("'Start verse' must be supplied if 'End verse' is specified.")
         return cleaned_data

    def make_reference(self):
        """
        Returns reference from cleaned_data, assuming forms validates.
        """
        reference = u"%s %s" % (self.cleaned_data['book'],
                                self.cleaned_data['start_chapter'])
        start_verse = self.cleaned_data['start_verse']
        if start_verse is not None:
            reference = u"%s:%s" % (reference, start_verse)
            end_verse = self.cleaned_data['end_verse']
            end_chapter = self.cleaned_data['end_chapter']
            if end_chapter is not None and end_verse is not None:
                reference = u"%s-%s:%s" % (reference, end_chapter, end_verse)
            elif end_verse is not None:
                reference =  u"%s-%s" % (reference, end_verse)
        return reference


class VerseSetForm(forms.ModelForm):
    class Meta:
        model = VerseSet
        fields = ('name', 'description', 'public')


a = VerseSetForm.base_fields['description'].widget.attrs
del a['cols']
a['rows'] = 3
VerseSetForm.base_fields['public'].label="Make public (can't be undone)"
