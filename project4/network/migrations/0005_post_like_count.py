# Generated by Django 4.2.5 on 2023-11-12 20:19

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('network', '0004_like'),
    ]

    operations = [
        migrations.AddField(
            model_name='post',
            name='like_count',
            field=models.IntegerField(default=0),
        ),
    ]