from django.contrib import admin

from .models import Local


@admin.register(Local)
class LocalAdmin(admin.ModelAdmin):
    list_display = ["nome", "endereco", "ativo"]
    list_filter = ["ativo"]
    search_fields = ["nome", "endereco"]
