# Generated by Django 4.2.11 on 2024-07-30 11:20

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('test_series', '0012_remove_question_exam_delete_userresponse'),
    ]

    operations = [
        migrations.DeleteModel(
            name='Question',
        ),
    ]
