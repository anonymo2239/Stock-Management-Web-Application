# Generated by Django 5.0.4 on 2024-12-25 14:26

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('processApp', '0004_alter_logadmin_options'),
    ]

    operations = [
        migrations.AlterField(
            model_name='logadmin',
            name='degisen',
            field=models.TextField(db_collation='Turkish_CI_AS', db_column='Degisen'),
        ),
    ]
