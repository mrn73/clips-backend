# Generated by Django 4.1.5 on 2023-03-23 04:34

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('videos', '0002_remove_video_file_size_remove_video_stored_at_and_more'),
    ]

    operations = [
        migrations.RenameField(
            model_name='video',
            old_name='creator_id',
            new_name='creator',
        ),
        migrations.AlterField(
            model_name='video',
            name='uploaded_at',
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
    ]
