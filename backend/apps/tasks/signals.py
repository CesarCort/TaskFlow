from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.utils import timezone
from .models import TaskVersion, TaskExecution

@receiver(post_save, sender=TaskVersion)
def update_task_last_version(sender, instance, created, **kwargs):
    """
    Actualiza el campo last_version en Task cuando se crea una nueva versión
    """
    if created and instance.status == 'active':
        instance.task.last_run = None
        instance.task.save()

@receiver(pre_save, sender=TaskExecution)
def update_task_last_run(sender, instance, **kwargs):
    """
    Actualiza el campo last_run en Task cuando se completa una ejecución
    """
    if instance.status == 'completed' and instance.completed_at:
        instance.task_version.task.last_run = timezone.now()
        instance.task_version.task.save()

@receiver(post_save, sender=TaskExecution)
def notify_execution_results(sender, instance, created, **kwargs):
    """
    Notifica los resultados de la ejecución
    """
    if not created and instance.status in ['completed', 'failed']:
        # Aquí iría la lógica de notificación
        # Por ejemplo, enviar un email, una notificación push, etc.
        pass 