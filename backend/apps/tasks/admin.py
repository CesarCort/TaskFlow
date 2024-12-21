from django.contrib import admin
from .models import Task, TaskVersion, TaskExecution

@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ('name', 'owner', 'status', 'is_public', 'last_run', 'created_at')
    list_filter = ('status', 'is_public', 'created_at')
    search_fields = ('name', 'description', 'owner__username')
    readonly_fields = ('created_at', 'updated_at', 'last_run')
    date_hierarchy = 'created_at'

@admin.register(TaskVersion)
class TaskVersionAdmin(admin.ModelAdmin):
    list_display = ('task', 'version_number', 'status', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('task__name', 'change_note')
    readonly_fields = ('created_at', 'updated_at')
    date_hierarchy = 'created_at'

@admin.register(TaskExecution)
class TaskExecutionAdmin(admin.ModelAdmin):
    list_display = ('task_version', 'status', 'started_at', 'completed_at', 'triggered_by')
    list_filter = ('status', 'started_at')
    search_fields = ('task_version__task__name', 'logs', 'error_message')
    readonly_fields = ('started_at', 'completed_at')
    date_hierarchy = 'started_at' 