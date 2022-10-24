import json

from django.db.models import QuerySet
from django.urls import reverse
from django.utils.http import urlencode
from django.utils.safestring import mark_safe

from .models import Component, Landing
from .service import AdminComponentGetter, JsonComponentGetter


class BaseAdminJson:
    field_name = None

    def __init__(self, obj):
        self.obj = obj

    def json_dump(self, obj, **kwargs) -> str:
        return json.dumps(obj, indent=2, ensure_ascii=False, **kwargs)

    def to_representation(self):
        raise NotImplementedError()

    @property
    def representation(self):
        return self.to_representation()


class ComponentAdminJson(BaseAdminJson):
    model = Component
    add_another_component_reverse_name = "admin:component-create-extra-component"

    def add_another_component_url(self, component: Component):
        url = reverse(self.add_another_component_reverse_name)
        kwargs = {
            "landing_id": component.landing_id,
            "template_id": component.template_id,
            "parent_field_id": component.parent_field_id,
        }
        kwargs = {k: v for k, v in kwargs.items() if v}
        return f"{url}?{urlencode(kwargs)}"

    def get_admin_value_str(self, attribute):
        value = AdminComponentGetter(attribute.get_type(), attribute).get()

        if isinstance(value, Component):
            return ComponentAdminJson(value).representation

        if isinstance(value, QuerySet) and isinstance(value.first(), Component):
            components = value.all()
            components_repr = [
                ComponentAdminJson(component).representation for component in components
            ]
            add_another_link = (
                f"</code>"
                f"<a class='related-widget-wrapper-link change-related'"
                f" href='{self.add_another_component_url(components.first())}'"
                f" target='_blank'>"
                f"&ltAdd another&gt"
                f"</a>"
                f"<code>"
            )
            return components_repr + [{"+": add_another_link}]

        return f"</code><a class='related-widget-wrapper-link change-related' href='{attribute.get_admin_url()}?to_field=as_json&_popup=1' target='_blank'>{value}</a><code>"

    def to_representation(self):
        return {
            attribute.template.name: self.get_admin_value_str(attribute)
            for attribute in self.obj.attributes.all()
        }


class ComponentJson(ComponentAdminJson):
    def get_admin_value_str(self, attribute):
        value = JsonComponentGetter(attribute.get_type(), attribute).get()

        if isinstance(value, Component):
            return ComponentJson(value).representation

        if isinstance(value, QuerySet) and isinstance(value.first(), Component):
            return [
                ComponentJson(component).representation for component in value.all()
            ]

        if not isinstance(value, (list, dict)):
            return str(value)

        return value


class LandingAdminJson(BaseAdminJson):
    model = Landing

    def to_representation(self):
        data = {
            "landingCode": self.obj.template.name,
            "sections": [
                {
                    "order": i,
                    "type": str(component.template.component_template.name),
                    "data": ComponentAdminJson(component).representation,
                }
                for i, component in enumerate(self.obj.components.all(), start=1)
                if not component.parent_field
            ],
        }
        html = f"<pre><code>{self.json_dump(data)}</code></pre>"
        return mark_safe(html)


class LandingJson(LandingAdminJson):
    def to_representation(self):
        return {
            "landingCode": self.obj.template.name,
            "sections": [
                {
                    "order": i,
                    "type": str(component.template.component_template.name),
                    "data": ComponentJson(component).representation,
                }
                for i, component in enumerate(self.obj.components.all(), start=1)
                if not component.parent_field
            ],
        }
