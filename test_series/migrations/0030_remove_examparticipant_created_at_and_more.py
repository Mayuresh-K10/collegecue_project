# Generated by Django 4.2.15 on 2024-08-21 09:53

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('test_series', '0029_examparticipant'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='examparticipant',
            name='created_at',
        ),
        migrations.AddField(
            model_name='examparticipant',
            name='exam_started',
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name='examparticipant',
            name='email',
            field=models.EmailField(max_length=254, unique=True),
        ),
        migrations.AlterField(
            model_name='examparticipant',
            name='name',
            field=models.CharField(max_length=255),
        ),
    ]
