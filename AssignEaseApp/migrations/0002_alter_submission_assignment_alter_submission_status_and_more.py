# Generated by Django 4.0.3 on 2024-11-24 18:07

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('AssignEaseApp', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='submission',
            name='assignment',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='submissions', to='AssignEaseApp.assignment'),
        ),
        migrations.AlterField(
            model_name='submission',
            name='status',
            field=models.CharField(choices=[('submitted', 'Submitted'), ('checked', 'Checked'), ('reassigned', 'Reassigned'), ('rejected', 'Rejected')], max_length=50),
        ),
        migrations.AlterField(
            model_name='submission',
            name='student',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='submissions', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterUniqueTogether(
            name='submission',
            unique_together={('student', 'assignment', 'question')},
        ),
    ]
