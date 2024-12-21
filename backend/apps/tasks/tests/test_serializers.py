from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIRequestFactory
from ..models import Task, TaskVersion, TaskExecution
from ..serializers import TaskSerializer, TaskVersionSerializer, TaskExecutionSerializer

User = get_user_model()

class TaskSerializerTests(TestCase):
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
        self.factory = APIRequestFactory()
        self.request = self.factory.get('/')
        self.request.user = self.user

    def test_contains_expected_fields(self):
        serializer = TaskSerializer(instance=self.task, context={'request': self.request})
        data = serializer.data
        self.assertCountEqual(
            data.keys(),
            ['id', 'name', 'description', 'owner', 'status', 'is_public',
             'tags', 'last_run', 'created_at', 'updated_at', 'active_version']
        )

    def test_owner_field_content(self):
        serializer = TaskSerializer(instance=self.task, context={'request': self.request})
        self.assertEqual(serializer.data['owner'], self.user.username)

class TaskVersionSerializerTests(TestCase):
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
            file='test.py',
            version_number=1
        )
        self.factory = APIRequestFactory()
        self.request = self.factory.get('/')

    def test_contains_expected_fields(self):
        serializer = TaskVersionSerializer(
            instance=self.version,
            context={'request': self.request}
        )
        data = serializer.data
        self.assertCountEqual(
            data.keys(),
            ['id', 'task', 'version_number', 'file', 'file_url', 'status',
             'change_note', 'requirements', 'metadata', 'created_at', 'updated_at']
        )

class TaskExecutionSerializerTests(TestCase):
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
            file='test.py',
            version_number=1
        )
        self.execution = TaskExecution.objects.create(
            task_version=self.version,
            triggered_by=self.user
        )
        self.factory = APIRequestFactory()
        self.request = self.factory.get('/')
        self.request.user = self.user

    def test_contains_expected_fields(self):
        serializer = TaskExecutionSerializer(
            instance=self.execution,
            context={'request': self.request}
        )
        data = serializer.data
        self.assertCountEqual(
            data.keys(),
            ['id', 'task_version', 'task_name', 'version_number', 'status',
             'logs', 'error_message', 'metrics', 'started_at', 'completed_at',
             'triggered_by', 'triggered_by_username']
        )

    def test_read_only_fields(self):
        serializer = TaskExecutionSerializer(context={'request': self.request})
        self.assertTrue(all(
            field in serializer.Meta.read_only_fields
            for field in ['logs', 'error_message', 'metrics', 'started_at',
                         'completed_at', 'triggered_by', 'triggered_by_username']
        )) 