from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import FileExtensionValidator, FileExtensionValidator
from django.core.exceptions import ValidationError
from django.conf import settings
import hashlib

User = get_user_model()

class Task(models.Model):
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('paused', 'Paused'),
        ('archived', 'Archived'),
    ]

    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='tasks')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    is_public = models.BooleanField(default=False)
    tags = models.JSONField(default=dict, blank=True)
    last_run = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']
        verbose_name = 'Task'
        verbose_name_plural = 'Tasks'

    def __str__(self):
        return self.name

    def get_active_version(self):
        return self.versions.filter(status='active').first()

    def clean(self):
        if not self.name:
            raise ValidationError('Task name is required')

class TaskVersion(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('archived', 'Archived'),
    ]

    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='versions')
    version_number = models.IntegerField()
    file = models.FileField(
        upload_to='task_files/',
        validators=[FileExtensionValidator(allowed_extensions=['py', 'ipynb'])]
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    change_note = models.TextField(blank=True)
    requirements = models.TextField(blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    checksum = models.CharField(max_length=64, blank=True)  # SHA-256
    file_size = models.IntegerField(default=0)  # Tamaño en bytes
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['task', 'version_number']
        ordering = ['-version_number']
        verbose_name = 'Task Version'
        verbose_name_plural = 'Task Versions'

    def __str__(self):
        return f"{self.task.name} - v{self.version_number}"

    def save(self, *args, **kwargs):
        if not self.version_number:
            last_version = self.task.versions.order_by('-version_number').first()
            self.version_number = (last_version.version_number + 1) if last_version else 1

        if self.file:
            # Calcular checksum y tamaño
            self.file.seek(0)
            content = self.file.read()
            self.checksum = hashlib.sha256(content).hexdigest()
            self.file_size = self.file.size
            self.file.seek(0)

        if self.status == 'active':
            # Desactivar otras versiones activas
            self.task.versions.filter(status='active').update(status='archived')

        super().save(*args, **kwargs)

    def clean(self):
        if not self.file:
            raise ValidationError('File is required')
        
        if self.file.name.split('.')[-1] not in ['py', 'ipynb']:
            raise ValidationError('Only .py and .ipynb files are allowed')

        # Validar tamaño máximo (10MB)
        if self.file.size > 10 * 1024 * 1024:  # 10MB en bytes
            raise ValidationError('File size cannot exceed 10MB')

class TaskExecution(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('running', 'Running'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
        ('timeout', 'Timeout'),
    ]

    task_version = models.ForeignKey(TaskVersion, on_delete=models.CASCADE, related_name='executions')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    logs = models.TextField(blank=True)
    error_message = models.TextField(blank=True)
    metrics = models.JSONField(default=dict, blank=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    triggered_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='triggered_executions'
    )
    celery_task_id = models.CharField(max_length=255, blank=True)
    resources = models.JSONField(default=dict, blank=True)  # CPU, memoria, etc.

    class Meta:
        ordering = ['-started_at']
        verbose_name = 'Task Execution'
        verbose_name_plural = 'Task Executions'

    def __str__(self):
        return f"{self.task_version} - {self.started_at}"

    def clean(self):
        if self.completed_at and self.started_at and self.completed_at < self.started_at:
            raise ValidationError('Completion time cannot be before start time')