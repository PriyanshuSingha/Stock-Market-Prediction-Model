"""
predictor/migrations/0001_initial.py
Initial database migration.
"""

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='PredictionHistory',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('symbol', models.CharField(max_length=20)),
                ('company_name', models.CharField(blank=True, max_length=200)),
                ('model_used', models.CharField(choices=[
                    ('linear', 'Linear Regression'),
                    ('random_forest', 'Random Forest'),
                    ('lstm', 'LSTM Neural Network'),
                ], default='linear', max_length=20)),
                ('current_price', models.FloatField(blank=True, null=True)),
                ('price_change_pct', models.FloatField(blank=True, null=True)),
                ('r2_score', models.FloatField(blank=True, null=True)),
                ('mse', models.FloatField(blank=True, null=True)),
                ('rmse', models.FloatField(blank=True, null=True)),
                ('prediction_days', models.IntegerField(default=7)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('user', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='predictions',
                    to=settings.AUTH_USER_MODEL,
                )),
            ],
            options={
                'verbose_name': 'Prediction History',
                'verbose_name_plural': 'Prediction Histories',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='SearchLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('symbol', models.CharField(max_length=20)),
                ('searched_at', models.DateTimeField(auto_now_add=True)),
                ('success', models.BooleanField(default=True)),
                ('error_message', models.TextField(blank=True)),
                ('user', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='searches',
                    to=settings.AUTH_USER_MODEL,
                )),
            ],
            options={
                'ordering': ['-searched_at'],
            },
        ),
    ]
