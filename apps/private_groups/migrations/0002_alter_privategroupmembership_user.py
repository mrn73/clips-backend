# Generated by Django 4.1.5 on 2023-04-27 06:51

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('private_groups', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='privategroupmembership',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='private_memberships', to=settings.AUTH_USER_MODEL),
        ),
    ]