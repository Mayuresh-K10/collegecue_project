# Generated by Django 4.2.15 on 2024-08-29 09:59

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('test_series', '0030_remove_examparticipant_created_at_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='proctoringsession',
            name='status',
            field=models.CharField(choices=[('ongoing', 'Ongoing'), ('completed', 'Completed')], default='ongoing', max_length=50),
        ),
    ]
