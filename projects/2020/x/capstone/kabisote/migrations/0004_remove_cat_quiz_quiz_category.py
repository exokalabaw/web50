# Generated by Django 5.0 on 2024-01-27 17:55

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('kabisote', '0003_remove_quiz_category_cat_quiz_bookmark_follow'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='cat',
            name='quiz',
        ),
        migrations.AddField(
            model_name='quiz',
            name='category',
            field=models.ManyToManyField(to='kabisote.cat'),
        ),
    ]