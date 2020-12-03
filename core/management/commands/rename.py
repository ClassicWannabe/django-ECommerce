from django.core.management.base import BaseCommand
import os


class Command(BaseCommand):
    help = 'Renames a Django Project'

    def add_arguments(self, parser):
        parser.add_argument('new_project_name', type=str,
                            help='a new Django project name')

    def handle(self, *args, **kwargs):
        new_project_name = kwargs['new_project_name']

        files_to_rename = ['ECommerce/settings/base.py',
                           'ECommerce/wsgi.py', 'manage.py', 'core/management/commands/rename.py']
        folder_to_rename = 'ECommerce'

        for f in files_to_rename:
            with open(f, 'r') as file:
                filedata = file.read()

            filedata = filedata.replace('ECommerce', new_project_name)

            with open(f, 'w') as file:
                file.write(filedata)

        os.rename(folder_to_rename, new_project_name)

        self.stdout.write(self.style.SUCCESS(
            f'Project has been renamed to {new_project_name}'))
