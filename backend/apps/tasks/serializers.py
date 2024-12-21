from rest_framework import serializers
from .models import Task, TaskVersion, TaskExecution

class TaskVersionSerializer(serializers.ModelSerializer):
    file_url = serializers.SerializerMethodField()
    
    class Meta:
        model = TaskVersion
        fields = [
            'id', 'task', 'version_number', 'file', 'file_url',
            'status', 'change_note', 'requirements', 'metadata',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['version_number']

    def get_file_url(self, obj):
        if obj.file:
            return self.context['request'].build_absolute_uri(obj.file.url)
        return None

class TaskSerializer(serializers.ModelSerializer):
    active_version = TaskVersionSerializer(source='get_active_version', read_only=True)
    owner = serializers.ReadOnlyField(source='owner.username')

    class Meta:
        model = Task
        fields = [
            'id', 'name', 'description', 'owner', 'status',
            'is_public', 'tags', 'last_run', 'created_at',
            'updated_at', 'active_version'
        ]
        read_only_fields = ['created_at', 'updated_at', 'last_run', 'owner']

    def create(self, validated_data):
        validated_data['owner'] = self.context['request'].user
        return super().create(validated_data)

class TaskExecutionSerializer(serializers.ModelSerializer):
    task_name = serializers.CharField(source='task_version.task.name', read_only=True)
    version_number = serializers.IntegerField(source='task_version.version_number', read_only=True)
    triggered_by_username = serializers.CharField(source='triggered_by.username', read_only=True)

    class Meta:
        model = TaskExecution
        fields = [
            'id', 'task_version', 'task_name', 'version_number',
            'status', 'logs', 'error_message', 'metrics',
            'started_at', 'completed_at', 'triggered_by',
            'triggered_by_username'
        ]
        read_only_fields = [
            'logs', 'error_message', 'metrics', 'started_at',
            'completed_at', 'triggered_by', 'triggered_by_username'
        ]

    def create(self, validated_data):
        validated_data['triggered_by'] = self.context['request'].user
        return super().create(validated_data) 