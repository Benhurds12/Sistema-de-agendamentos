"""Cria um superusuario fixo, so para facilitar a avaliacao local do projeto.

Guardado atras de `DEBUG=True` de proposito: essa credencial e conhecida
publicamente (esta no README), entao nunca deveria existir num ambiente que
nao seja de desenvolvimento local.
"""

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError

USERNAME_PADRAO = "admin"
SENHA_PADRAO = "admin123"


class Command(BaseCommand):
    help = (
        "Cria o superusuario padrao de avaliacao "
        f"(usuario='{USERNAME_PADRAO}', senha='{SENHA_PADRAO}'). "
        "Nao faz nada se o usuario ja existir. So roda com DEBUG=True."
    )

    def handle(self, *args, **options):
        if not settings.DEBUG:
            raise CommandError(
                "Este comando so pode ser executado com DEBUG=True "
                "(ambiente de desenvolvimento local)."
            )

        User = get_user_model()

        if User.objects.filter(username=USERNAME_PADRAO).exists():
            self.stdout.write(
                self.style.WARNING(f"Usuario '{USERNAME_PADRAO}' ja existe. Nada a fazer.")
            )
            return

        User.objects.create_superuser(username=USERNAME_PADRAO, password=SENHA_PADRAO)
        self.stdout.write(
            self.style.SUCCESS(
                f"Superusuario '{USERNAME_PADRAO}' criado com sucesso "
                f"(senha: '{SENHA_PADRAO}')."
            )
        )
