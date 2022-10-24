from django.db.models import Manager


class ComponentObjectGetter:
    default_when_undefined = None

    def __init__(self, enum_value, obj):
        self.enum_value = enum_value
        self.obj = obj

    def _getter_bool(self):
        return (
            self.default_when_undefined
            if self.obj.value_bool is None
            else self.obj.value_bool
        )

    def _getter_object(self):
        lookup = self.obj.value_object_field or self.obj.template.name

        landing_object = self.obj.component.landing.object
        value = getattr(landing_object, lookup, self.default_when_undefined)

        return list(value.all()) if isinstance(value, Manager) else value

    def _getter_default(self):
        return (
            getattr(self.obj, f"value_{self.enum_value}", self.default_when_undefined)
            or self.default_when_undefined
        )

    def get(self):
        enum_value = self.enum_value.lower()
        getter = getattr(self, f"_getter_{enum_value}", self._getter_default)
        return getter()


class AdminComponentGetter(ComponentObjectGetter):
    default_when_undefined = "&ltempty&gt"

    def _getter_components(self):
        value = self._getter_default()
        return value.all()


class JsonComponentGetter(ComponentObjectGetter):
    default_when_undefined = ""

    def _getter_components(self):
        value = self._getter_default()
        return value.all()
