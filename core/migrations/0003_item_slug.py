# Generated by Django 3.1.3 on 2020-11-27 08:37

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0002_auto_20201127_1305'),
    ]

    operations = [
        migrations.AddField(
            model_name='item',
            name='slug',
            field=models.SlugField(default='product-slug'),
            preserve_default=False,
        ),
    ]