import os
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User, Group


class Command(BaseCommand):
    help = 'Crea o actualiza los usuarios y grupos iniciales del sistema'

    def handle(self, *args, **options):
        # Grupos del sistema
        grupos_nombres = ['Gerencia', 'RRHH', 'Contabilidad', 'Logistica', 'ingenieria']
        grupos = {}
        for nombre in grupos_nombres:
            g, _ = Group.objects.get_or_create(name=nombre)
            grupos[nombre] = g

        usuarios_datos = [
            {
                'username': 'admin',
                'password': os.environ.get('ADMIN_PASSWORD', 'AdwiN!23$5Io6Lk'),
                'email': 'admin@cointeca.com',
                'is_staff': True,
                'is_superuser': True,
                'grupos': ['Gerencia'],
            },
            {
                'username': 'gerente',
                'password': os.environ.get('GERENTE_PASSWORD', 'Ge34%#2/6ju('),
                'email': 'gerente@cointeca.com',
                'is_staff': True,
                'is_superuser': True,
                'grupos': ['Gerencia'],
            },
            {
                'username': 'rrhh',
                'password': os.environ.get('RRHH_PASSWORD', 'rrHH&5$57(#4'),
                'email': 'rrhh@cointeca.com',
                'is_staff': True,
                'is_superuser': False,
                'grupos': ['RRHH'],
            },
            {
                'username': 'contabilidad',
                'password': os.environ.get('CONTABILIDAD_PASSWORD', 'C0nt4i3yL/)2'),
                'email': 'contabilidad@cointeca.com',
                'is_staff': True,
                'is_superuser': False,
                'grupos': ['Contabilidad'],
            },
            {
                'username': 'logistica',
                'password': os.environ.get('LOGISTICA_PASSWORD', 'L0&i$T/c4#&'),
                'email': 'logistica@cointeca.com',
                'is_staff': True,
                'is_superuser': False,
                'grupos': ['Logistica'],
            },
            {
                'username': 'ingenieria',
                'password': os.environ.get('INGENIERIA_PASSWORD', 'In6n13#E$5ria'),
                'email': 'ingenieria@cointeca.com',
                'is_staff': True,
                'is_superuser': False,
                'grupos': ['ingenieria'],
            },
        ]

        for udata in usuarios_datos:
            user, created = User.objects.get_or_create(
                username=udata['username'],
                defaults={
                    'email': udata['email'],
                    'is_staff': udata['is_staff'],
                    'is_superuser': udata['is_superuser'],
                }
            )
            # Asegura contraseña y permisos
            user.set_password(udata['password'])
            user.is_staff = udata['is_staff']
            user.is_superuser = udata['is_superuser']
            user.save()

            # Asignar grupos
            for g_name in udata['grupos']:
                user.groups.add(grupos[g_name])

            estado = 'creado' if created else 'actualizado'
            self.stdout.write(self.style.SUCCESS(f"Usuario '{user.username}' {estado} con éxito."))

        self.stdout.write(self.style.SUCCESS("¡Todos los usuarios iniciales han sido configurados!"))
