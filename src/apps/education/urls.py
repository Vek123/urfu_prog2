from django.urls import path

from . import auth_views, monitoring, web_views

from .views import (DisciplineCollectionView, DisciplineDetailView,
                    StudentCollectionView, StudentDetailView)

app_name = 'education'
urlpatterns = [
    path('', auth_views.IndexView.as_view(), name='home'),
    path('index', auth_views.IndexView.as_view(), name='index'),
    path('register', auth_views.RegistrationView.as_view(), name='register'),
    path('register/save', auth_views.RegistrationSaveView.as_view(), name='register-save'),
    path('login', auth_views.LoginView.as_view(), name='login'),
    path('logout', auth_views.LogoutView.as_view(), name='logout'),
    path('users', auth_views.UsersView.as_view(), name='users'),
    path('api/students', StudentCollectionView.as_view(), name='student-list'),
    path('api/students/<int:item_id>', StudentDetailView.as_view(), name='student-detail'),
    path('api/disciplines', DisciplineCollectionView.as_view(), name='discipline-list'),
    path('api/disciplines/<int:item_id>', DisciplineDetailView.as_view(), name='discipline-detail'),
    path('list', web_views.ResourceListView.as_view(kind='students'), name='web-student-list'),
    path('addStudentForm', web_views.ResourceAddView.as_view(kind='students'), name='web-student-add'),
    path('saveStudent', web_views.ResourceSaveView.as_view(kind='students'), name='web-student-save'),
    path('showUpdateForm', web_views.ResourceEditView.as_view(kind='students'), name='web-student-edit'),
    path('deleteStudent', web_views.ResourceDeleteView.as_view(kind='students'), name='web-student-delete'),
    path('groups', web_views.ResourceListView.as_view(kind='groups'), name='web-group-list'),
    path('addGroupForm', web_views.ResourceAddView.as_view(kind='groups'), name='web-group-add'),
    path('saveGroup', web_views.ResourceSaveView.as_view(kind='groups'), name='web-group-save'),
    path('showGroupUpdateForm', web_views.ResourceEditView.as_view(kind='groups'), name='web-group-edit'),
    path('deleteGroup', web_views.ResourceDeleteView.as_view(kind='groups'), name='web-group-delete'),
    path('actuator', monitoring.ActuatorIndexView.as_view(), name='actuator-index'),
    path('actuator/health', monitoring.HealthView.as_view(), name='actuator-health'),
    path('actuator/info', monitoring.InfoView.as_view(), name='actuator-info'),
    path('actuator/metrics', monitoring.MetricsView.as_view(), name='actuator-metrics'),
    path('actuator/metrics/<str:metric_name>', monitoring.MetricsView.as_view(), name='actuator-metric'),
]
