from django.contrib import admin

from .models import Atendimento, HorarioAgendamento


@admin.register(HorarioAgendamento)
class HorarioAgendamentoAdmin(admin.ModelAdmin):
    """Permite excluir horarios gerados por engano (ex.: feriado, fim de
    semana) sem precisar de acesso direto ao banco. `date_hierarchy` deixa
    facil navegar ate um dia especifico e selecionar/excluir em lote.

    Horarios ja vinculados a um Atendimento nao podem ser excluidos aqui —
    o `on_delete=PROTECT` do model bloqueia isso automaticamente.
    """

    list_display = ["local", "inicio", "fim", "disponivel"]
    list_filter = ["local", "disponivel"]
    date_hierarchy = "inicio"
    ordering = ["-inicio"]


@admin.register(Atendimento)
class AtendimentoAdmin(admin.ModelAdmin):
    list_display = ["cliente", "local", "tipo", "data_hora", "status"]
    list_filter = ["status", "local", "tipo"]
    search_fields = ["cliente__nome"]
    date_hierarchy = "data_hora"
    ordering = ["-data_hora"]
