import tempfile
import shutil

from django.test import TestCase, Client, override_settings
from django.urls import reverse
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.cache import cache

from ..models import Post, Group, Follow, User
from ..forms import PostForm


TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostPagesTest(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        # Создаем пользователя
        cls.user = User.objects.create_user(username='auth')
        # Для тестирования загрузки изображений
        # берём байт-последовательность картинки,
        # состоящей из двух пикселей: белого и чёрного
        cls.small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        cls.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=cls.small_gif,
            content_type='image/gif'
        )
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
            group=cls.group,
            image=cls.uploaded
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
        cls.REVERSE_FOLLOW_INDEX = reverse('posts:follow_index')

    @classmethod
    def tearDownClass(cls) -> None:
        super().tearDownClass()
        # Метод shutil.rmtree удаляет директорию и всё её содержимое
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.user_followed = User.objects.create_user(username='Followed')
        # Создаем неавторизованный клиент
        self.guest_client = Client()
        # Создаем авторизованный клиент
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        # Создаем авторизованный клиент, который ни на кого не подписан
        self.not_follower = Client()
        self.not_follower.force_login(self.user_followed)

    def tearDown(self) -> None:
        cache.clear()

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_pages_names = {
            self.REVERSE_INDEX: 'posts/index.html',
            self.REVERSE_GROUP_LIST: 'posts/group_list.html',
            self.REVERSE_PROFILE: 'posts/profile.html',
            self.REVERSE_POST_DETAIL: 'posts/post_detail.html',
            self.REVERSE_POST_EDIT: 'posts/create_post.html',
            self.REVERSE_POST_CREATE: 'posts/create_post.html',
        }
        for reverse_name, template in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_pages_with_posts_show_correct_context(self):
        """Шаблоны с постами отображают ожидаемый контекст."""
        # Создаем словарь с reverse_name и ожидаемым контекстом
        reverse_expected_context = {
            self.REVERSE_INDEX: list(Post.objects.all()),
            self.REVERSE_GROUP_LIST: (
                list(Post.objects.filter(group_id=self.group.id))
            ),
            self.REVERSE_PROFILE: (
                list(Post.objects.filter(author_id=self.user.id))
            ),
        }
        for reverse_name, expected_value in reverse_expected_context.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                response_object = list(response.context['page_obj'])
                self.assertEqual(response_object, expected_value)

    def test_post_detail_page_show_correct_context(self):
        """Пост отфильтрованный по id в шаблоне
        post_detail соответсвует контексту."""
        response = self.authorized_client.get(
            self.REVERSE_POST_DETAIL)
        expected = Post.objects.get(id=self.post.id)
        self.assertEqual(response.context['post'], expected)

    def test_post_edit_and_create_pages_show_correct_context(self):
        """Шаблоны post_edit и post_create
        сформированы с правильным контекстом"""
        url_names = (
            self.REVERSE_POST_EDIT,
            self.REVERSE_POST_CREATE,
        )
        for reverse_name in url_names:
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(
                    reverse_name
                )
                self.assertIsInstance(response.context['form'], PostForm)
                if 'is_edit' in response.context.keys():
                    self.assertTrue(response.context['is_edit'])
                    self.assertEqual(response.context['post'], self.post)

    def test_post_with_group_on_right_pages(self):
        """Проверяем, что пост с указанной группой отображается:
        на главной странице сайта,
        на странице выбранной группы,
        в профайле пользователя."""
        result = Post.objects.get(group=self.post.group)
        check_pages = (
            self.REVERSE_INDEX,
            self.REVERSE_GROUP_LIST,
            self.REVERSE_PROFILE
        )
        for page in check_pages:
            with self.subTest(page=page):
                response = self.authorized_client.get(page)
                response_obj = response.context['page_obj']
                self.assertIn(result, response_obj)

    def test_post_with_group_not_in_wrong_group_list(self):
        """Проверяем, что пост с указанной группой не попал в группу,
        для которой не был предназначен."""
        group_1 = Group.objects.create(
            title='Тест_группа_1',
            slug='test_slug_1',
            description='Тестовое_описание_1',
        )
        result = Post.objects.get(group=self.post.group)
        response = self.authorized_client.get(
            reverse('posts:group_list', kwargs={'slug': group_1.slug})
        )
        self.assertNotIn(result, response.context['page_obj'])

    def test_images_on_right_pages(self):
        """Проверяет, что при выводе поста с картинкой
        изображение передаётся в словаре context:
        на главную страницу,
        на страницу профайла,
        на страницу группы."""
        # Перечень страниц на которых должна отобразится картинка
        url_with_images = (
            self.REVERSE_INDEX,
            self.REVERSE_GROUP_LIST,
            self.REVERSE_PROFILE,
        )
        for reverse_name in url_with_images:
            with self.subTest(reverse_name=reverse_name):
                response = self.guest_client.get(reverse_name)
                result = response.context.get('page_obj')[0].image
                self.assertEqual(result, self.post.image)

    def test_image_on_post_detail_page(self):
        """Проверяет, что при выводе поста с картинкой
        изображение передаётся в словаре context
        на отдельную страницу поста."""
        response = self.guest_client.get(self.REVERSE_POST_DETAIL)
        self.assertEqual(response.context['post'].image, self.post.image)

    def test_cache_on_index_page(self):
        """Проверяет работу кэш на странице index.html."""
        post_cache = Post.objects.create(
            author=self.user,
            text='test_cache'
        )
        response = self.guest_client.get(self.REVERSE_INDEX)
        response_content = response.content
        Post.objects.get(id=post_cache.id).delete()
        cache_data = self.guest_client.get(self.REVERSE_INDEX)
        # Проверяем, что после удаления поста данные сохранены в кэше
        self.assertEqual(cache_data.content, response_content)
        # Проверяем, что после очистки кэша данные удалены
        cache.clear()
        cache_delete = self.guest_client.get(self.REVERSE_INDEX)
        self.assertNotEqual(cache_delete.content, response_content)

    def test_autorized_client_follow_unfollow(self):
        """Авторизованный пользователь может:
        - подписываться на других пользователей
        - удалять других пользователей из подписок."""
        self.authorized_client.get(
            reverse('posts:profile_follow',
                    args=(self.user_followed,)))
        self.assertTrue(
            Follow.objects.filter(
                user=self.user
            ).filter(
                author=self.user_followed
            ).exists()
        )
        self.authorized_client.get(
            reverse('posts:profile_unfollow', args=(self.user_followed,))
        )
        self.assertFalse(
            Follow.objects.filter(
                user=self.user
            ).filter(
                author=self.user_followed
            ).exists()
        )

    def test_new_post_on_follower_page(self):
        """Новая запись пользователя:
        - появляется в ленте тех, кто на него подписан
        - не появляется в ленте тех, кто не подписан."""
        # Создаем подписку на user_followed у authorized_client
        Follow.objects.create(
            user=self.user,
            author=self.user_followed
        )
        post_followed = Post.objects.create(
            author=self.user_followed,
            text='test_text_followed'
        )
        # Проверяем, что post_followed отобразился у user
        response = self.authorized_client.get(reverse('posts:follow_index'))
        self.assertContains(response, post_followed.text)
        # Проверяем, что post_followed не отобразился у user_followed
        # т.к. user_followed не подписан на user_followed
        response1 = self.not_follower.get(reverse('posts:follow_index'))
        self.assertNotContains(response1, post_followed.text)
