
from django.contrib import admin, messages
from django.contrib.contenttypes.models import ContentType
from django.http import HttpResponse
from django.urls import path

from .admin_helpers import LandingAdminJson
from .admin_inlines import (
    AttributeInline,
    AttributeTemplateInline,
    LandingTemplateItemInline,
)
from .models import Attribute
from .models import AttributeTemplate
from .models import Component
from .models import ComponentTemplate
from .models import Landing
from .models import LandingTemplate
from .utils import (
    get_required_field_names,
)


class AttributeAdmin(admin.ModelAdmin):
    model = Attribute

    readonly_fields = [
        "landing",
        "template_name",
    ]
    list_display = [
        "id",
        "landing",
        "get_component_template",
        "template_name",
        "value_str",
    ]
    list_display_links = ["value_str"]
    list_filter = [
        "component__landing",
        "component__template__component_template",
        "component__parent_field__template__child_obj_template",
    ]

    def landing(self, obj):
        return obj.get_landing()

    def get_fields(self, request, obj=None):
        if not obj:
            return get_required_field_names(self.model, include_m2m=False)
        return ["template_name"] + obj.get_typed_fields()

    def template_name(self, obj):
        return obj.template.name


class ComponentAdmin(admin.ModelAdmin):
    inlines = [AttributeInline]


@admin.register(ContentType)
class ContentTypeAdmin(admin.ModelAdmin):
    search_fields = ("model",)


class LandingAdmin(admin.ModelAdmin):
    readonly_fields = [
        "obj_repr",
        "as_json",
    ]
    autocomplete_fields = (
        "template",
        "object_ctype",
    )

    def obj_repr(self, obj):
        return repr(obj.object)

    def as_json(self, obj: Landing):
        return LandingAdminJson(obj).representation

    def custom_admin_view(self, request):
        attrs = ["landing_id", "template_id", "parent_field_id"]
        kwargs = {name: request.GET.get(name, None) for name in attrs}

        Component.objects.create(**kwargs)
        messages.info(request, message="An extra component has been created")
        return HttpResponse(
            "An extra component has been created. Close this window and reload page."
        )

    def get_urls(self):
        additional_urls = [
            path(
                "create-component/",
                self.admin_site.admin_view(self.custom_admin_view),
                name="component-create-extra-component",
            )
        ]
        return additional_urls + super().get_urls()


class AttributeTemplateAdmin(admin.ModelAdmin):
    list_filter = ["component_template__name"]


class ComponentTemplateAdmin(admin.ModelAdmin):
    inlines = [AttributeTemplateInline]


@admin.register(LandingTemplate)
class LandingTemplateAdmin(admin.ModelAdmin):
    search_fields = ("name",)
    inlines = [LandingTemplateItemInline]


admin.site.register(Landing, LandingAdmin)
admin.site.register(Attribute, AttributeAdmin)
admin.site.register(Component, ComponentAdmin)

admin.site.register(ComponentTemplate, ComponentTemplateAdmin)
admin.site.register(AttributeTemplate, AttributeTemplateAdmin)
