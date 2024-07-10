# Generated by Django 4.2.13 on 2024-05-29 09:23

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0007_userregistration_delete_customuser'),
    ]

    operations = [
        migrations.CreateModel(
            name='ContactMessage',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('email', models.EmailField(max_length=254)),
                ('phone', models.CharField(max_length=15)),
                ('message', models.TextField()),
            ],
        ),
    ]