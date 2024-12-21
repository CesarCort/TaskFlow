from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import TaskViewSet, TaskVersionViewSet, TaskExecutionViewSet

router = DefaultRouter()
router.register(r'tasks', TaskViewSet, basename='task')
router.register(r'versions', TaskVersionViewSet, basename='taskversion')
router.register(r'executions', TaskExecutionViewSet, basename='taskexecution')

urlpatterns = [
    path('', include(router.urls)),
] 