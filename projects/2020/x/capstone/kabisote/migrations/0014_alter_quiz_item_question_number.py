# Generated by Django 5.0 on 2024-02-19 06:05

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('kabisote', '0013_alter_quiz_item_options_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='quiz_item',
            name='question_number',
            field=models.IntegerField(),
        ),
    ]
