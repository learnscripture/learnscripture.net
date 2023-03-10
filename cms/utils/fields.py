from django.db import models

from .widgets import CmsTextarea


class CmsTextField(models.TextField):
    def formfield(self, **kwargs):
        defaults = {"widget": CmsTextarea}
        defaults.update(kwargs)
        return super().formfield(**defaults)


class CmsHTMLField(CmsTextField):
    pass
