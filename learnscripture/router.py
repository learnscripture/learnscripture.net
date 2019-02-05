from django.conf import settings


class LearnScriptureRouter(object):
    def is_word_suggestion_model(self, app_label, model_name):
        return app_label == "bibleverses" and model_name == "wordsuggestiondata"

    def db_for_read(self, model, **hints):
        return (settings.DB_LABEL_WORDSUGGESTIONS
                if self.is_word_suggestion_model(model._meta.app_label, model.__name__.lower())
                else settings.DB_LABEL_DEFAULT)

    def db_for_write(self, model, **hints):
        return self.db_for_read(model, **hints)

    def allow_relation(self, obj1, obj2, **hints):
        return None

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        if 'target_dbs' in hints:
            return db in hints['target_dbs']
        return ((db == settings.DB_LABEL_WORDSUGGESTIONS)
                if model_name is not None and self.is_word_suggestion_model(app_label, model_name)
                else (db == settings.DB_LABEL_DEFAULT))
