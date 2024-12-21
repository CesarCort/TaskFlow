from rest_framework import viewsets, status, decorators
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser
from django.utils import timezone
from django.db import transaction
from django.core.files.uploadedfile import UploadedFile
import requirements
from io import StringIO
from .models import Task, TaskVersion, TaskExecution
from .serializers import TaskSerializer, TaskVersionSerializer, TaskExecutionSerializer
from .tasks import execute_task

class TaskViewSet(viewsets.ModelViewSet):
    serializer_class = TaskSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return Task.objects.filter(owner=user) | Task.objects.filter(is_public=True)

    @decorators.action(detail=True, methods=['post'])
    def execute(self, request, pk=None):
        task = self.get_object()
        active_version = task.get_active_version()
        
        if not active_version:
            return Response(
                {'error': 'No active version found for this task'},
                status=status.HTTP_400_BAD_REQUEST
            )

        with transaction.atomic():
            execution = TaskExecution.objects.create(
                task_version=active_version,
                triggered_by=request.user,
                started_at=timezone.now()
            )
            
            # Iniciar tarea asíncrona
            celery_task = execute_task.delay(execution.id)
            execution.celery_task_id = celery_task.id
            execution.save()

            task.last_run = timezone.now()
            task.save()

        return Response(TaskExecutionSerializer(execution).data)

class TaskVersionViewSet(viewsets.ModelViewSet):
    serializer_class = TaskVersionSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = (MultiPartParser, FormParser)

    def get_queryset(self):
        return TaskVersion.objects.filter(task__owner=self.request.user)

    @decorators.action(detail=False, methods=['post'])
    def upload(self, request):
        """
        Endpoint para subir archivos de tarea
        """
        if 'file' not in request.FILES:
            return Response(
                {'error': 'No file provided'},
                status=status.HTTP_400_BAD_REQUEST
            )

        file = request.FILES['file']
        task_id = request.data.get('task')

        try:
            task = Task.objects.get(id=task_id, owner=request.user)
        except Task.DoesNotExist:
            return Response(
                {'error': 'Task not found or access denied'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Validar extensión
        if not file.name.endswith(('.py', '.ipynb')):
            return Response(
                {'error': 'Invalid file type. Only .py and .ipynb files are allowed'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Validar tamaño
        if file.size > 10 * 1024 * 1024:  # 10MB
            return Response(
                {'error': 'File size exceeds 10MB limit'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Detectar dependencias si es archivo Python
        requirements_text = ''
        if file.name.endswith('.py'):
            content = file.read().decode('utf-8')
            file.seek(0)
            try:
                # Parsear imports
                import ast
                tree = ast.parse(content)
                imports = [node for node in ast.walk(tree) if isinstance(node, ast.Import) or isinstance(node, ast.ImportFrom)]
                requirements_text = '\n'.join(node.names[0].name.split('.')[0] for node in imports)
            except:
                pass

        # Crear nueva versión
        version = TaskVersion.objects.create(
            task=task,
            file=file,
            requirements=requirements_text
        )

        return Response(
            TaskVersionSerializer(version, context={'request': request}).data,
            status=status.HTTP_201_CREATED
        )

    @decorators.action(detail=True, methods=['post'])
    def activate(self, request, pk=None):
        version = self.get_object()
        
        with transaction.atomic():
            # Desactivar todas las otras versiones
            version.task.versions.exclude(pk=version.pk).update(status='archived')
            version.status = 'active'
            version.save()

        return Response(TaskVersionSerializer(version, context={'request': request}).data)

    def perform_create(self, serializer):
        if not serializer.validated_data.get('task').owner == self.request.user:
            return Response(
                {'error': 'You can only create versions for your own tasks'},
                status=status.HTTP_403_FORBIDDEN
            )
        serializer.save()

class TaskExecutionViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = TaskExecutionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return TaskExecution.objects.filter(
            task_version__task__owner=self.request.user
        )

    @decorators.action(detail=True)
    def logs(self, request, pk=None):
        execution = self.get_object()
        return Response({'logs': execution.logs})

    @decorators.action(detail=True)
    def metrics(self, request, pk=None):
        execution = self.get_object()
        return Response(execution.metrics)

    @decorators.action(detail=True)
    def status(self, request, pk=None):
        """
        Obtener estado detallado de la ejecución
        """
        execution = self.get_object()
        
        data = {
            'status': execution.status,
            'started_at': execution.started_at,
            'completed_at': execution.completed_at,
            'logs': execution.logs,
            'error_message': execution.error_message,
            'metrics': execution.metrics,
            'resources': execution.resources,
        }

        # Si está en ejecución, obtener métricas en tiempo real
        if execution.status == 'running' and execution.celery_task_id:
            from celery.result import AsyncResult
            task = AsyncResult(execution.celery_task_id)
            data['task_status'] = task.status
            
            # Obtener información del proceso si está disponible
            try:
                import psutil
                process = psutil.Process(task.worker.pid)
                data['current_resources'] = {
                    'cpu_percent': process.cpu_percent(),
                    'memory_percent': process.memory_percent(),
                    'memory_info': dict(process.memory_info()._asdict())
                }
            except:
                pass

        return Response(data)

    @decorators.action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """
        Cancelar una ejecución en curso
        """
        execution = self.get_object()
        
        if execution.status != 'running':
            return Response(
                {'error': 'Only running executions can be cancelled'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if execution.celery_task_id:
            from celery.result import AsyncResult
            task = AsyncResult(execution.celery_task_id)
            task.revoke(terminate=True)

        execution.status = 'cancelled'
        execution.completed_at = timezone.now()
        execution.save()

        return Response({'status': 'cancelled'}) 