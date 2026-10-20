from django.urls import path

from .views import (DisciplineCollectionView, DisciplineDetailView,
                    StudentCollectionView, StudentDetailView)

app_name = 'education'
urlpatterns = [
    path('api/students', StudentCollectionView.as_view(), name='student-list'),
    path('api/students/<int:item_id>', StudentDetailView.as_view(), name='student-detail'),
    path('api/disciplines', DisciplineCollectionView.as_view(), name='discipline-list'),
    path('api/disciplines/<int:item_id>', DisciplineDetailView.as_view(), name='discipline-detail'),
]
