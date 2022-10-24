from enum import Enum

from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.db.models.base import ModelBase
from django.utils.module_loading import import_string


class StrEnum(str, Enum):
    @classmethod
    def choices(cls):
        return [(key.value, key.name) for key in cls]

    @staticmethod
    def _generate_next_value_(name, start, count, last_values):
        return name.lower()


class UpperStrEnum(StrEnum):
    @staticmethod
    def _generate_next_value_(name, start, count, last_values):
        return name.upper()


def get_admin_fields(model: ModelBase):
    for field in model._meta.get_fields():
        # Skip id
        if field.name == "id":
            continue

        if isinstance(field, GenericForeignKey):
            continue

        yield field


def get_editable_admin_fields(model: ModelBase):
    for field in model._meta.get_fields():
        # Skip id
        if field.name == "id":
            continue

        if isinstance(field, GenericForeignKey):
            continue

        if field.one_to_many or field.one_to_one or field.many_to_many:
            continue

        yield field


def get_required_fields_iterator(model: ModelBase, include_m2m=False):
    for field in model._meta.get_fields():
        # Skip id
        if field.name == "id":
            continue

        if isinstance(field, GenericForeignKey):
            continue

        if not include_m2m and (
            (field.one_to_many or field.one_to_one or field.many_to_many)
            and field.auto_created
            and not field.concrete
        ):
            continue

        required = not getattr(field, "blank", False)

        if required:
            yield field


def get_required_fields(model, include_m2m=False):
    return list(get_required_fields_iterator(model, include_m2m=include_m2m))


def get_required_field_names(model, include_m2m=False):
    return list(
        map(
            lambda f: f.name,
            get_required_fields_iterator(model, include_m2m=include_m2m),
        )
    )


def get_default_jpg_image_mapping():
    return import_string(settings.COMPONENTS_DEFAULT_JPG_IMAGE_MAPPING)


def get_default_png_image_mapping():
    return import_string(settings.COMPONENTS_DEFAULT_PNG_IMAGE_MAPPING)


def value_is_relation(value):
    return hasattr(value, "field")


def value_is_file(value):
    return hasattr(value, "file")


def value_is_m2m(value):
    return hasattr(value, "field") and value.field.many_to_many

