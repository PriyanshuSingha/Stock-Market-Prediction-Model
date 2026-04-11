from django.contrib import admin
from .models import PredictionHistory, SearchLog


@admin.register(PredictionHistory)
class PredictionHistoryAdmin(admin.ModelAdmin):
    list_display  = ('user', 'symbol', 'model_used', 'current_price', 'r2_score', 'created_at')
    list_filter   = ('model_used', 'created_at')
    search_fields = ('user__username', 'symbol', 'company_name')
    ordering      = ('-created_at',)


@admin.register(SearchLog)
class SearchLogAdmin(admin.ModelAdmin):
    list_display  = ('user', 'symbol', 'searched_at', 'success')
    list_filter   = ('success', 'searched_at')
    search_fields = ('user__username', 'symbol')
