# Generated by Django 5.0.6 on 2024-08-17 22:44

from django.conf import settings
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('voting', '0002_candidate_bio_vote_voter_is_anonymous_and_more'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='vote',
            unique_together={('voting_event', 'voter')},
        ),
    ]
