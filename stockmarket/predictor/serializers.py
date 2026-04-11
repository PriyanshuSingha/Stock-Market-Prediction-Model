"""
predictor/serializers.py
DRF serializers for user authentication and prediction history.
"""

from django.contrib.auth.models import User
from rest_framework import serializers
from .models import PredictionHistory


class RegisterSerializer(serializers.ModelSerializer):
    password  = serializers.CharField(write_only=True, min_length=8)
    password2 = serializers.CharField(write_only=True, label='Confirm Password')

    class Meta:
        model  = User
        fields = ('username', 'email', 'first_name', 'last_name', 'password', 'password2')

    def validate(self, data):
        if data['password'] != data['password2']:
            raise serializers.ValidationError({'password': 'Passwords do not match.'})
        return data

    def create(self, validated_data):
        validated_data.pop('password2')
        return User.objects.create_user(**validated_data)


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model  = User
        fields = ('id', 'username', 'email', 'first_name', 'last_name', 'date_joined')


class PredictionHistorySerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model  = PredictionHistory
        fields = (
            'id', 'username', 'symbol', 'company_name', 'model_used',
            'current_price', 'price_change_pct',
            'r2_score', 'mse', 'rmse',
            'prediction_days', 'created_at',
        )
