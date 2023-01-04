# posts/tests/test_urls.py
from http import HTTPStatus

from django.test import TestCase, Client
from django.urls import reverse

from ..models import Post, Group, User


class PostUrlTests(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        # Создаем пользователя
        cls.user = User.objects.create_user(username='auth')
        # Создаем неавторизованный клиент
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
        )
        cls.REVERSE_INDEX = reverse('posts:index')
        cls.REVERSE_GROUP_LIST = (
            reverse('posts:group_list', kwargs={'slug': cls.group.slug})
        )
        cls.REVERSE_PROFILE = (
            reverse('posts:profile', kwargs={'username': cls.post.author})
        )
        cls.REVERSE_POST_DETAIL = (
            reverse('posts:post_detail', kwargs={'post_id': cls.post.id})
        )
        cls.REVERSE_POST_EDIT = (
            reverse('posts:post_edit', kwargs={'post_id': cls.post.id})
        )
        cls.REVERSE_POST_CREATE = reverse('posts:post_create')
        cls.UNEXISTING_PAGE = '/unexisting_page/'

    def setUp(self):
        # Создаем неавторизованный клиент
        self.guest_client = Client()
        # Создаем пользователя
        self.user_not_author = User.objects.create_user(username='HasNoName')
        # Создаем второй клиент
        self.authorized_client = Client()
        # Авторизуем пользователя
        self.authorized_client.force_login(self.user_not_author)
        # Создаем Автора
        self.author = Client()
        self.author.force_login(self.user)

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        # Шаблоны по адресам
        templates_url_names = {
            self.REVERSE_INDEX: 'posts/index.html',
            self.REVERSE_GROUP_LIST: 'posts/group_list.html',
            self.REVERSE_PROFILE: 'posts/profile.html',
            self.REVERSE_POST_DETAIL: 'posts/post_detail.html',
            self.REVERSE_POST_EDIT: 'posts/create_post.html',
            self.REVERSE_POST_CREATE: 'posts/create_post.html',
        }
        for address, template in templates_url_names.items():
            with self.subTest(address=address):
                response = self.author.get(address)
                self.assertTemplateUsed(response, template)

    def test_guest_client_post_html_pages_available(self):
        """Проверяет доступ к страницам Posts у неавторизованного клиента."""
        # Создаем словарь url: HTTPStatus для guest_client
        url_guest_client_status = {
            self.REVERSE_INDEX: HTTPStatus.OK,
            self.REVERSE_GROUP_LIST: HTTPStatus.OK,
            self.REVERSE_PROFILE: HTTPStatus.OK,
            self.REVERSE_POST_DETAIL: HTTPStatus.OK,
            self.REVERSE_POST_EDIT: HTTPStatus.FOUND,
            self.REVERSE_POST_CREATE: HTTPStatus.FOUND,
            self.UNEXISTING_PAGE: HTTPStatus.NOT_FOUND,
        }
        for address, status in url_guest_client_status.items():
            with self.subTest(address=address):
                response = self.guest_client.get(address)
                self.assertEqual(response.status_code, status)

    def test_authorized_client_post_html_pages_available(self):
        """Проверяет доступ к страницам Posts у авторизованного клиента."""
        # Создаем словарь url: HTTPStatus для authorized_client
        url_authorized_client_status = {
            self.REVERSE_INDEX: HTTPStatus.OK,
            self.REVERSE_GROUP_LIST: HTTPStatus.OK,
            self.REVERSE_PROFILE: HTTPStatus.OK,
            self.REVERSE_POST_DETAIL: HTTPStatus.OK,
            self.REVERSE_POST_EDIT: HTTPStatus.FOUND,
            self.REVERSE_POST_CREATE: HTTPStatus.OK,
            self.UNEXISTING_PAGE: HTTPStatus.NOT_FOUND,
        }
        for address, status in url_authorized_client_status.items():
            with self.subTest(address=address):
                response = self.authorized_client.get(address)
                self.assertEqual(response.status_code, status)

    def test_author_post_html_pages_available(self):
        """Проверяет доступ к страницам Posts у Автора."""
        # Создаем словарь url: HTTPStatus для author
        url_author_status = {
            self.REVERSE_INDEX: HTTPStatus.OK,
            self.REVERSE_GROUP_LIST: HTTPStatus.OK,
            self.REVERSE_PROFILE: HTTPStatus.OK,
            self.REVERSE_POST_DETAIL: HTTPStatus.OK,
            self.REVERSE_POST_EDIT: HTTPStatus.OK,
            self.REVERSE_POST_CREATE: HTTPStatus.OK,
            self.UNEXISTING_PAGE: HTTPStatus.NOT_FOUND,
        }
        for address, status in url_author_status.items():
            with self.subTest(address=address):
                response = self.author.get(address)
                self.assertEqual(response.status_code, status)
