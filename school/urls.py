from django.urls import path
from . import views

app_name = 'school'

urlpatterns = [
    path('api/teacher/dashboard/', views.teacher_dashboard, name='teacher_dashboard'),
    path('api/teacher/assignment/<int:assignment_id>/student/<int:student_id>/semester/<int:semester_id>/grade/add/',
         views.add_grade, name='add_grade'),

    # Новий маршрут для учня:
    path('api/student/dashboard/', views.student_dashboard, name='student_dashboard'),
]