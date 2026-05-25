from django.contrib import admin
from django.urls import path, include # Додано include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('school.urls')), # Підключаємо маршрути додатку school
]