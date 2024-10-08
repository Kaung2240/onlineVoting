# Generated by Django 5.0.6 on 2024-08-18 19:25

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('voting', '0005_alter_votingevent_created_by'),
    ]

    operations = [
        migrations.CreateModel(
            name='Category',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
            ],
        ),
        migrations.AddField(
            model_name='votingevent',
            name='categories',
            field=models.ManyToManyField(to='voting.category'),
        ),
    ]
