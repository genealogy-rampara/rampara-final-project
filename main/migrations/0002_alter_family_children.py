# Generated by Django 4.2.13 on 2024-05-24 11:06

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='family',
            name='children',
            field=models.ManyToManyField(related_name='families', to='main.person'),
        ),
    ]