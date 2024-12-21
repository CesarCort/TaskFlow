from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APIClient
from rest_framework import status
from unittest.mock import patch
from ..models import Task, TaskVersion, TaskExecution
from ..tasks import execute_task

User = get_user_model()

class TaskViewSetTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)
        self.task = Task.objects.create(
            name='Test Task',
            owner=self.user,
            description='Test Description'
        )

    def test_list_tasks(self):
        response = self.client.get('/api/tasks/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_create_task(self):
        data = {
            'name': 'New Task',
            'description': 'New Description'
        }
        response = self.client.post('/api/tasks/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Task.objects.count(), 2)
        self.assertEqual(response.data['name'], 'New Task')

    @patch('apps.tasks.tasks.execute_task.delay')
    def test_execute_task(self, mock_execute):
        version = TaskVersion.objects.create(
            task=self.task,
            file='test.py',
            status='active'
        )
        response = self.client.post(f'/api/tasks/{self.task.id}/execute/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(TaskExecution.objects.count(), 1)
        mock_execute.assert_called_once()

class TaskVersionViewSetTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)
        self.task = Task.objects.create(
            name='Test Task',
            owner=self.user
        )
        self.test_file = SimpleUploadedFile(
            "test.py",
            b"print('hello world')",
            content_type="text/plain"
        )

    def test_upload_valid_file(self):
        data = {
            'task': self.task.id,
            'file': self.test_file
        }
        response = self.client.post('/api/versions/upload/', data, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(TaskVersion.objects.count(), 1)
        version = TaskVersion.objects.first()
        self.assertTrue(version.checksum)
        self.assertEqual(version.file_size, len(b"print('hello world')"))

    def test_upload_invalid_extension(self):
        invalid_file = SimpleUploadedFile(
            "test.txt",
            b"invalid file",
            content_type="text/plain"
        )
        data = {
            'task': self.task.id,
            'file': invalid_file
        }
        response = self.client.post('/api/versions/upload/', data, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(TaskVersion.objects.count(), 0)

    def test_upload_file_too_large(self):
        large_content = b'x' * (10 * 1024 * 1024 + 1)  # 10MB + 1 byte
        large_file = SimpleUploadedFile(
            "large.py",
            large_content,
            content_type="text/plain"
        )
        data = {
            'task': self.task.id,
            'file': large_file
        }
        response = self.client.post('/api/versions/upload/', data, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(TaskVersion.objects.count(), 0)

    def test_activate_version(self):
        version = TaskVersion.objects.create(
            task=self.task,
            file='test.py'
        )
        response = self.client.post(f'/api/versions/{version.id}/activate/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        version.refresh_from_db()
        self.assertEqual(version.status, 'active')

class TaskExecutionViewSetTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)
        self.task = Task.objects.create(
            name='Test Task',
            owner=self.user
        )
        self.version = TaskVersion.objects.create(
            task=self.task,
            file='test.py'
        )
        self.execution = TaskExecution.objects.create(
            task_version=self.version,
            triggered_by=self.user,
            celery_task_id='test-task-id'
        )

    def test_list_executions(self):
        response = self.client.get('/api/executions/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_get_execution_logs(self):
        self.execution.logs = "Test logs"
        self.execution.save()
        response = self.client.get(f'/api/executions/{self.execution.id}/logs/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['logs'], "Test logs")

    def test_get_execution_metrics(self):
        self.execution.metrics = {'cpu': 50, 'memory': 100}
        self.execution.save()
        response = self.client.get(f'/api/executions/{self.execution.id}/metrics/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, {'cpu': 50, 'memory': 100})

    def test_get_execution_status(self):
        response = self.client.get(f'/api/executions/{self.execution.id}/status/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('status', response.data)
        self.assertIn('metrics', response.data)
        self.assertIn('resources', response.data)

    @patch('celery.result.AsyncResult')
    def test_cancel_execution(self, mock_async_result):
        self.execution.status = 'running'
        self.execution.save()
        response = self.client.post(f'/api/executions/{self.execution.id}/cancel/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.execution.refresh_from_db()
        self.assertEqual(self.execution.status, 'cancelled')
        mock_async_result.assert_called_once_with('test-task-id') 