from django.contrib import admin

from .models import TipoAtendimento


@admin.register(TipoAtendimento)
class TipoAtendimentoAdmin(admin.ModelAdmin):
    list_display = ["nome", "duracao_minutos", "ativo"]
    list_filter = ["ativo"]
    search_fields = ["nome"]
