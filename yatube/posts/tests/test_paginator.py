from django.test import Client, TestCase
from django.urls import reverse

from ..models import Group, Post, User
from ..views import VIEW_ELEMENTS

POST_AMOUNT = VIEW_ELEMENTS + 1


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.user = User.objects.create_user(username='TBD')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        for i in range(POST_AMOUNT):
            cls.post = Post.objects.create(
                author=cls.user,
                text=f'Test_post_{i}',
                group=cls.group
            )
        cls.REVERSE_INDEX = reverse('posts:index')
        cls.REVERSE_GROUP_LIST = (
            reverse('posts:group_list', kwargs={'slug': cls.group.slug})
        )
        cls.REVERSE_PROFILE = (
            reverse('posts:profile', kwargs={'username': cls.post.author})
        )
        cls.check_pages = (
            cls.REVERSE_INDEX,
            cls.REVERSE_GROUP_LIST,
            cls.REVERSE_PROFILE
        )

    def setUp(self) -> None:
        # Создаем авторизованный клиент
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_first_page_contain_correct_amount_of_posts(self):
        """Проверяет что количество постов на первой странице равно
        VIEW_ELEMENTS."""
        for reverse_name in self.check_pages:
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertEqual(len(response.context['page_obj']),
                                 VIEW_ELEMENTS)

    def test_second_page_contain_correct_amount_of_posts(self):
        """Проверяет что количество постов на второй стронице равно
        POST_AMOUNT - VIEW_ELEMENTS."""
        for reverse_name in self.check_pages:
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name + '?page=2')
                self.assertEqual(
                    len(response.context['page_obj']),
                    POST_AMOUNT - VIEW_ELEMENTS
                )
