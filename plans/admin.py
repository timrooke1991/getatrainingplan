from django.contrib import admin
from .models import Template, TemplateVersion, Response
from django_ace import AceWidget
from django.db import models


class TemplateVersionInline(admin.TabularInline):
    model = TemplateVersion
    extra = 0
    readonly_fields = ("created_at",)


class TemplateAdmin(admin.ModelAdmin):
    inlines = [TemplateVersionInline]


class TemplateVersionAdmin(admin.ModelAdmin):
    list_display = ("pk", "template", "created_at")
    list_filter = ("template",)
    search_fields = ("template__name",)

    formfield_overrides = {
        models.TextField: {"widget": AceWidget(mode="django", theme="monokai")}
    }

    def save_model(self, request, obj, form, change):
        if change:
            # Create a new version if editing an existing TemplateVersion instance
            obj.pk = None
        super().save_model(request, obj, form, change)


@admin.register(Response)
class ResponseAdmin(admin.ModelAdmin):
    list_display = ["id", "template", "template_version", "response", "token_length"]
    list_filter = ["template", "template_version"]
    search_fields = ["response"]
    readonly_fields = ["id"]


admin.site.register(Template, TemplateAdmin)
admin.site.register(TemplateVersion, TemplateVersionAdmin)
