from django.urls import path
from . import views

app_name = 'school'

urlpatterns = [
    # API для виставлення оцінки
    path('api/teacher/dashboard/', views.teacher_dashboard, name='teacher_dashboard'),
    path('api/teacher/assignment/<int:assignment_id>/student/<int:student_id>/semester/<int:semester_id>/grade/add/',
         views.add_grade, name='add_grade'),

    # НОВІ МАРШРУТИ T2 (Редагування та видалення)
    path('api/teacher/grade/<int:grade_id>/edit/', views.edit_grade, name='edit_grade'),
    path('api/teacher/grade/<int:grade_id>/delete/', views.delete_grade, name='delete_grade'),

    path('api/student/dashboard/', views.student_dashboard, name='student_dashboard'),
    path('api/teacher/assignment/<int:assignment_id>/journal-data/', views.get_journal_data, name='get_journal_data'),

    # Маршрути для HTML-сторінок
    path('teacher/', views.teacher_page, name='teacher_page'),
    path('student/', views.student_page, name='student_page'),

    # НОВИЙ МАРШРУТ (Вирішення проблеми відсутності сторінки класного керівника)
    # Ми використовуємо той самий teacher_page, оскільки він вже містить потрібний інтерфейс
    path('homeroom/', views.teacher_page, name='homeroom_page'),

    # Експорт звіту вчителя (T3)
    path('api/teacher/assignment/<int:assignment_id>/export/', views.export_grades_csv, name='export_grades_csv'),

    # API класного керівника (K1)
    path('api/homeroom/dashboard/', views.homeroom_dashboard_api, name='homeroom_dashboard_api'),
]