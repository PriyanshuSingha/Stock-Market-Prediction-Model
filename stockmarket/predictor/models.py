"""
predictor/models.py
Database models for Stock Market Prediction system.
"""

from django.db import models
from django.contrib.auth.models import User


class PredictionHistory(models.Model):
    """Stores every prediction request made by users."""

    MODEL_CHOICES = [
        ('linear', 'Linear Regression'),
        ('random_forest', 'Random Forest'),
        ('lstm', 'LSTM Neural Network'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='predictions')
    symbol = models.CharField(max_length=20)
    company_name = models.CharField(max_length=200, blank=True)
    model_used = models.CharField(max_length=20, choices=MODEL_CHOICES, default='linear')
    current_price = models.FloatField(null=True, blank=True)
    price_change_pct = models.FloatField(null=True, blank=True)
    r2_score = models.FloatField(null=True, blank=True)
    mse = models.FloatField(null=True, blank=True)
    rmse = models.FloatField(null=True, blank=True)
    prediction_days = models.IntegerField(default=7)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Prediction History'
        verbose_name_plural = 'Prediction Histories'

    def __str__(self):
        return f"{self.user.username} → {self.symbol} [{self.model_used}] @ {self.created_at:%Y-%m-%d %H:%M}"


class SearchLog(models.Model):
    """Logs every symbol search for analytics."""

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='searches')
    symbol = models.CharField(max_length=20)
    searched_at = models.DateTimeField(auto_now_add=True)
    success = models.BooleanField(default=True)
    error_message = models.TextField(blank=True)

    class Meta:
        ordering = ['-searched_at']

    def __str__(self):
        return f"{self.user.username} searched {self.symbol}"
