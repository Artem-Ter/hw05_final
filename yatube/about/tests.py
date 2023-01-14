from http import HTTPStatus

from django.test import TestCase, Client
from django.urls import reverse


class StaticURLTests(TestCase):
    def setUp(self):
        # Устанавливаем данные для тестирования
        # Создаём экземпляр клиента. Он неавторизован.
        self.guest_client = Client()

    def test_unathorized_client_about_pages_available(self):
        """Проверяет доступ к страницам about у неавторизованного клиента."""
        # Создаем картеж из reverse_names
        reverse_names = (
            reverse('about:author'),
            reverse('about:tech')
        )
        for url in reverse_names:
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)
