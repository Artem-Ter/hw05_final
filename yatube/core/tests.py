from http import HTTPStatus

from django.test import TestCase, Client


class ViewTestClass(TestCase):
    def setUp(self) -> None:
        # Создаем невторизованный клиент
        self.guest_client = Client()

    def test_error_page(self):
        response = self.guest_client.get('/nonexist-page/')
        # Проверяем, что статус ответа сервера - 404
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        # Проверьте, что используется шаблон core/404.html
        self.assertTemplateUsed(response, 'core/404.html')
