from django import forms

from bibleverses.models import BIBLE_BOOKS, VerseSet, parse_ref


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

    def __init__(self, data=None, **kwargs):
        if 'verse_list' in kwargs:
            verse_list = kwargs.pop('verse_list')
            if data is None:
                data = {}

            ref_start = parse_ref(verse_list[0].reference, None, return_verses=False)
            ref_end = parse_ref(verse_list[-1].reference, None, return_verses=False)
            if isinstance(ref_start, tuple):
                ref_start = ref_start[0]
            if isinstance(ref_end, tuple):
                ref_end = ref_end[1]
            data['book'] = ref_start.book
            data['start_chapter'] = ref_start.chapter_number

            # Special case complete chapters - just put chapter number
            if (ref_end.chapter_number != ref_start.chapter_number or
                ref_start.verse_number != 1 or
                not verse_list[-1].is_last_verse_in_chapter()):

                data['start_verse'] = ref_start.verse_number
                data['end_chapter'] = ref_end.chapter_number
                data['end_verse'] = ref_end.verse_number

            if 'prefix' in kwargs:
                data2 = {}
                prefix = kwargs['prefix']
                for k, v in data.items():
                    data2['%s-%s' % (prefix, k)] = v
                data = data2

        super(PassageVerseSelector, self).__init__(data=data, **kwargs)


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
