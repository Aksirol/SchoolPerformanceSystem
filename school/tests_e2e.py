from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from django.contrib.auth import get_user_model
import datetime

from .models import Teacher, SchoolClass, AcademicYear, Subject, TeacherSubject

User = get_user_model()

class TeacherInterfaceE2ETest(StaticLiveServerTestCase):
    # Зверніть увагу: ми прибрали host='0.0.0.0'.
    # За замовчуванням Django використає 'localhost', і Chrome успішно збереже cookie сесії.

    def setUp(self):
        # Налаштування невидимого браузера Chrome
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--window-size=1920,1080")

        self.driver = webdriver.Chrome(options=chrome_options)
        self.driver.implicitly_wait(5)

        # Підготовка тестових даних
        self.user_teacher = User.objects.create_user(
            username='teacher_e2e',
            password='password123',
            role='teacher',
            is_staff=True
        )
        self.teacher = Teacher.objects.create(
            user=self.user_teacher, first_name='Ігор', last_name='Петренко', email='igor@test.com'
        )

        year = AcademicYear.objects.create(name='2023-2024', start_date=datetime.date(2023, 9, 1), end_date=datetime.date(2024, 5, 31))
        school_class = SchoolClass.objects.create(name='11-А', grade_number=11, academic_year=year)
        subject = Subject.objects.create(name='Астрономія')

        TeacherSubject.objects.create(teacher=self.teacher, subject=subject, school_class=school_class)

    def tearDown(self):
        self.driver.quit()

    def test_teacher_dashboard_loads_assignments(self):
        """Перевірка E2E: Вчитель логіниться і бачить картку свого предмета"""

        # 1. Авторизація
        self.driver.get(f"{self.live_server_url}/admin/login/")
        self.driver.find_element(By.NAME, "username").send_keys("teacher_e2e")
        self.driver.find_element(By.NAME, "password").send_keys("password123")
        self.driver.find_element(By.CSS_SELECTOR, "input[type='submit']").click()

        # Чекаємо успішного входу
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.ID, "user-tools"))
        )

        # 2. Перехід на фронтенд вчителя
        self.driver.get(f"{self.live_server_url}/teacher/")

        # 3. Перевіряємо наявність заголовка (з використанням явного очікування)
        header_element = WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "h3"))
        )
        self.assertIn("Мої предмети та класи", header_element.text)

        # 4. Чекаємо, поки JS зробить fetch-запит і відмалює картки
        subject_card_title = WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//h5[contains(@class, 'card-title') and contains(text(), 'Астрономія')]"))
        )

        self.assertEqual(subject_card_title.text, 'Астрономія')