from django.contrib import admin

from .models import Attribute, AttributeTemplate, ComponentTemplate, LandingTemplateItem


class AttributeInline(admin.TabularInline):
    model = Attribute
    fk_name = "component"

    fields = readonly_fields = ["template", "get_type", "value_str"]
    show_change_link = True

    extra = 0


class AttributeTemplateInline(admin.TabularInline):
    model = AttributeTemplate
    fk_name = "component_template"


class ComponentTemplateInline(admin.TabularInline):
    model = ComponentTemplate
    show_change_link = True

    extra = 0


class LandingTemplateItemInline(admin.TabularInline):
    model = LandingTemplateItem
