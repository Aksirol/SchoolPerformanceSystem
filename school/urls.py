from django.urls import path
from . import views

app_name = 'school'

urlpatterns = [
    # Наші API маршрути...
    path('api/teacher/dashboard/', views.teacher_dashboard, name='teacher_dashboard'),
    path('api/teacher/assignment/<int:assignment_id>/student/<int:student_id>/semester/<int:semester_id>/grade/add/',
         views.add_grade, name='add_grade'),
    path('api/student/dashboard/', views.student_dashboard, name='student_dashboard'),
    path('api/teacher/assignment/<int:assignment_id>/journal-data/', views.get_journal_data, name='get_journal_data'),

    # Нові маршрути для HTML-сторінок фронтенду:
    path('teacher/', views.teacher_page, name='teacher_page'),
    path('student/', views.student_page, name='student_page'),

    # Експорт звіту вчителя (T3)
    path('api/teacher/assignment/<int:assignment_id>/export/', views.export_grades_csv, name='export_grades_csv'),

    # API класного керівника (K1)
    path('api/homeroom/dashboard/', views.homeroom_dashboard_api, name='homeroom_dashboard_api'),
]