from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from ..models import Task, TaskVersion, TaskExecution

User = get_user_model()

class TaskModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.task = Task.objects.create(
            name='Test Task',
            owner=self.user,
            description='Test Description'
        )

    def test_task_creation(self):
        self.assertEqual(self.task.name, 'Test Task')
        self.assertEqual(self.task.owner, self.user)
        self.assertEqual(self.task.status, 'active')
        self.assertFalse(self.task.is_public)

    def test_task_str(self):
        self.assertEqual(str(self.task), 'Test Task')

    def test_task_get_active_version(self):
        self.assertIsNone(self.task.get_active_version())

class TaskVersionModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.task = Task.objects.create(
            name='Test Task',
            owner=self.user
        )

    def test_version_number_auto_increment(self):
        version1 = TaskVersion.objects.create(
            task=self.task,
            file='test1.py',
            version_number=1
        )
        version2 = TaskVersion.objects.create(
            task=self.task,
            file='test2.py'
        )
        self.assertEqual(version2.version_number, 2)

    def test_only_one_active_version(self):
        version1 = TaskVersion.objects.create(
            task=self.task,
            file='test1.py',
            status='active'
        )
        version2 = TaskVersion.objects.create(
            task=self.task,
            file='test2.py',
            status='active'
        )
        version1.refresh_from_db()
        self.assertEqual(version1.status, 'archived')
        self.assertEqual(version2.status, 'active')

class TaskExecutionModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.task = Task.objects.create(
            name='Test Task',
            owner=self.user
        )
        self.version = TaskVersion.objects.create(
            task=self.task,
            file='test.py'
        )

    def test_execution_creation(self):
        execution = TaskExecution.objects.create(
            task_version=self.version,
            triggered_by=self.user
        )
        self.assertEqual(execution.status, 'pending')
        self.assertEqual(execution.triggered_by, self.user)

    def test_execution_str(self):
        execution = TaskExecution.objects.create(
            task_version=self.version,
            triggered_by=self.user
        )
        self.assertIn(str(self.version), str(execution)) 