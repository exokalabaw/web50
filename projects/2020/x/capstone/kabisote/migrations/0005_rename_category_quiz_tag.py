# Generated by Django 5.0 on 2024-01-28 07:23

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('kabisote', '0004_remove_cat_quiz_quiz_category'),
    ]

    operations = [
        migrations.RenameField(
            model_name='quiz',
            old_name='category',
            new_name='tag',
        ),
    ]
