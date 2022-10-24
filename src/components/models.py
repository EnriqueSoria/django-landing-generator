from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.urls import reverse

from .abstract_models import AbstractAttribute
from .enumerations import ComponentType


class AttributeTemplate(models.Model):
    name = models.CharField(max_length=125)
    value_type = models.CharField(max_length=75, choices=ComponentType.choices())

    # this attribute holds a component list, these components must be of this type
    child_obj_template = models.ForeignKey(
        "ComponentTemplate",
        on_delete=models.CASCADE,
        blank=True,
        null=True,
    )

    component_template = models.ForeignKey(
        "ComponentTemplate", on_delete=models.CASCADE, related_name="attributes"
    )

    @property
    def path(self):
        return (
            f"{self.component_template.name}_{self.component_template.pk}/{self.name}"
        )

    def __str__(self):
        return f"{self.component_template.name}.{self.name}"


class ComponentTemplate(models.Model):
    name = models.CharField(max_length=125)

    def __str__(self):
        return f"{self.name}"


class LandingTemplateItem(models.Model):
    component_template = models.ForeignKey(
        "ComponentTemplate", on_delete=models.CASCADE
    )
    landing_template = models.ForeignKey(
        "LandingTemplate", on_delete=models.CASCADE, related_name="items", null=True
    )

    def __str__(self):
        return f"{self.landing_template}[{self.pk}].{self.component_template}"

    class Meta:
        order_with_respect_to = "landing_template"


class LandingTemplate(models.Model):
    name = models.CharField(max_length=200)

    def __str__(self):
        return self.name


# ---


class Attribute(AbstractAttribute):
    component = models.ForeignKey(
        "Component", on_delete=models.CASCADE, related_name="attributes"
    )
    template = models.ForeignKey("AttributeTemplate", on_delete=models.CASCADE)

    value_component = models.OneToOneField(
        "Component",
        on_delete=models.CASCADE,
        related_name="attribute_parent",  # don't change! see: AbstractAttribute.value
        null=True,
        blank=True,
    )

    @property
    def path(self):
        return f"/{self.component.path}/{self.template.path}_{self.pk}"

    def get_component_template(self) -> "ComponentTemplate":
        if self.component.parent_field:
            return self.component.parent_field.template.child_obj_template

        return self.component.template.component_template

    def get_component(self) -> "Component":
        if self.component.parent_field:
            return self.component.parent_field.component

        return self.component

    def get_landing(self) -> "Landing":
        return self.get_component().landing

    def create_component_children(self, number=1):
        if self.get_type() == ComponentType.COMPONENT:
            component, created = Component.objects.get_or_create(
                landing=self.component.landing, template=None, parent_field=self
            )
            if created:
                component.save()
                self.value_component = component
                self.save()

        if self.get_type() == ComponentType.COMPONENTS:
            for _ in range(number):
                self.value_components.get_or_create(
                    template=None, landing=self.component.landing, parent_field=self
                )

    def get_type(self):
        return self.template.value_type

    def get_admin_url(self):
        return reverse(
            "admin:%s_%s_change" % (self._meta.app_label, self._meta.model_name),
            args=[self.id],
        )

    def __str__(self):
        if self.component.parent_field:
            return f"{self.component}[{self.component_id}].{self.template}"

        return f"{self.component}.{self.template}"

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)


class Component(models.Model):
    landing = models.ForeignKey(
        "Landing", on_delete=models.CASCADE, related_name="components"
    )
    template = models.ForeignKey(
        "LandingTemplateItem", on_delete=models.CASCADE, null=True
    )

    parent_field = models.ForeignKey(
        "Attribute",
        on_delete=models.CASCADE,
        related_name="value_components",  # don't change! see: AbstractAttribute.value
        null=True,
        blank=True,
    )

    class Meta:
        unique_together = ("landing", "template")

    @property
    def path(self):
        return f"{self.landing.path}_{self.pk}"

    def __str__(self):
        if self.parent_field:
            return f"{self.parent_field}."
        return f"{self.landing}[{self.pk}].{self.template.component_template}"

    def get_component_template(self) -> ComponentTemplate:
        """This component's template"""
        if self.parent_field:
            return self.parent_field.template.child_obj_template

        return self.template.component_template

    def get_attribute_templates(self):
        """Get attribute templates for this component"""
        return self.get_component_template().attributes.all()

    def create_attributes(self):
        """Create attributes for this component"""
        for attr_template in self.get_attribute_templates():
            attr, __ = self.attributes.get_or_create(
                component=attr_template.component_template, template=attr_template
            )

            attr.create_component_children(number=1)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.create_attributes()


class Landing(models.Model):
    template = models.ForeignKey("LandingTemplate", on_delete=models.CASCADE)

    # To which object is related
    object_ctype = models.ForeignKey(
        ContentType, on_delete=models.CASCADE, null=True, blank=True
    )
    object_pk = models.PositiveIntegerField(null=True, blank=True)
    object = GenericForeignKey("object_ctype", "object_pk")

    class Meta:
        unique_together = ("template", "object_ctype", "object_pk")

    @property
    def path(self):
        return f"landing/{self.object_ctype}"

    def __str__(self):
        return f"Landing({self.object_ctype}={self.object})"

    def create_components(self):
        for item in self.template.items.all():
            self.components.get_or_create(template=item)

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
        self.create_components()
