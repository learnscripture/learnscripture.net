
class LearnScriptureRouter(object):
    def is_word_suggestion_model(self, model):
        return model._meta.app_label == "bibleverses" and model.__name__ == "WordSuggestionData"

    def db_for_read(self, model, **hints):
        return "wordsuggestions" if self.is_word_suggestion_model(model) else "default"

    def db_for_write(self, model, **hints):
        return self.db_for_read(model, **hints)

    def allow_relation(self, obj1, obj2, **hints):
        return None

    def allow_syncdb(self, db, model):
        return (db == "wordsuggestions") if self.is_word_suggestion_model(model) else (db == "default")
