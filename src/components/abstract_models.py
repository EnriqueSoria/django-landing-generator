import json

from django.db import models
from django.utils.text import slugify

from .enumerations import ComponentType
from .service import ComponentObjectGetter
from .utils import value_is_file
from .utils import value_is_relation


class AbstractAttribute(models.Model):
    # text
    value_text = models.TextField(null=True, blank=True)

    # int
    value_int = models.IntegerField(null=True, blank=True)

    # url
    value_url = models.URLField(max_length=400, null=True, blank=True)

    # bool
    value_bool = models.BooleanField(null=True, blank=True)

    # image
    value_png = models.ImageField(
        null=True,
        blank=True
    )
    value_jpg = models.ImageField(
        null=True,
        blank=True,
    )

    # object
    value_object_field = models.CharField(max_length=200, blank=True, null=True)

    def get_type(self):
        raise NotImplementedError()

    @property
    def value(self):
        return ComponentObjectGetter(self.get_type(), self).get()

    @value.setter
    def value(self, value):
        field_type = self.get_type()
        if field_type == ComponentType.OBJECT:
            raise AttributeError("Can't set value to field type 'OBJECT'")
        setattr(self, "value_%s" % field_type, value)

    @property
    def value_str(self):
        if not self.value:
            return None
        if value_is_file(self.value):
            return str(self.value)
        if value_is_relation(self.value):
            return str(self.value.values_list("id", flat=True))
        return str(self.value)

    def __str__(self):
        v = self.value_str
        if isinstance(v, dict):
            return json.dumps(v, ensure_ascii=False)
        return str(v)

    @property
    def slug(self):
        return slugify(str(self))

    def get_field_names(self):
        return [field.name for field in self._meta.get_fields()]

    def get_typed_fields(self, include_relations=False):
        return [
            field.name
            for field in self._meta.get_fields()
            if self.get_type() in field.name and not value_is_relation(field)
        ]

    class Meta:
        abstract = True
