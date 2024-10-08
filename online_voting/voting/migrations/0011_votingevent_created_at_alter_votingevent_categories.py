# Generated by Django 5.1 on 2024-08-25 06:58

import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('voting', '0010_profile'),
    ]

    operations = [
        migrations.AddField(
            model_name='votingevent',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='votingevent',
            name='categories',
            field=models.ManyToManyField(related_name='events', to='voting.category'),
        ),
    ]
