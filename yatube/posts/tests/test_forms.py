# posts/tests/test_forms.py
import tempfile
import shutil

from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from django.conf import settings

from ..models import Post, Group, User


TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostCreateFormTest(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.user = User.objects.create_user(username='HasNoName')
        cls.post = Post.objects.create(
            author=cls.user,
            text='test_text_1'
        )
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
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
        cls.REVERSE_POST_DETAIL = (
            reverse('posts:post_detail', kwargs={'post_id': cls.post.id})
        )
        cls.REVERSE_ADD_COMMENT = (
            reverse('posts:add_comment', kwargs={'post_id': cls.post.id})
        )

    @classmethod
    def tearDownClass(cls) -> None:
        super().tearDownClass()
        # Метод shutil.rmtree удаляет директорию и всё её содержимое
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self) -> None:
        # Создаем невторизованный клиент.
        self.guest_client = Client()
        # Создаем авторизованный клиент.
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_create_post(self):
        """Проверяет, что при отправке валидной формы
        со страницы создания поста reverse('posts:post_create')
        создаётся новая запись в базе данных"""
        # Подсчитаем количество записей в Post
        posts_count = Post.objects.count()
        form_data = {
            'text': 'test_text',
            'group': self.group.id,
            'image': self.uploaded
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        # Проверяем, сработал ли редирект
        self.assertRedirects(
            response,
            reverse('posts:profile', kwargs={'username': self.user.username})
        )
        # Проверяем, увеличилось ли число постов
        self.assertEqual(Post.objects.count(), posts_count + 1)
        # Проверяем, что создалась запись с заданным текстом и группой
        self.assertTrue(
            Post.objects.filter(
                text='test_text',
                group_id=self.group.id,
                image=f'posts/{self.uploaded.name}'
            ).exists()
        )

    def test_post_edit(self):
        """Проверяет, что при отправке валидной формы со страницы
        редактирования поста reverse('posts:post_edit', args=('post_id',)),
        происходит изменение поста с post_id в базе данных."""
        # Подсчитаем количество записей в Post
        posts_count = Post.objects.count()
        form_data = {
            'text': 'edited_text',
            'group': self.group.id,
        }
        response = self.authorized_client.post(
            reverse('posts:post_edit', args=(self.post.id,)),
            data=form_data,
            follow=True,
        )
        # Проверяем, сработал ли редирект
        self.assertRedirects(
            response,
            self.REVERSE_POST_DETAIL
        )
        # Проверяем, что число постов не изменилось
        self.assertEqual(Post.objects.count(), posts_count)
        # Проверяем, что запись с измененным текстом и группой существует
        self.assertTrue(
            Post.objects.filter(
                text='edited_text',
                group_id=self.group.id
            ).exists()
        )

    def test_add_comment(self):
        """Проверяет, что после успешной отправки комментарий:
        - авторизованного пользователя появляется на странице поста
        - не авториованного пользователя не появляется на странице поста"""
        # Подсчитываем количество комментариев у поста
        comment_count = self.post.comments.count()
        # Создаем словарь ключь - пользователь
        # занчение - redirect_url, comment_text,
        # add_comment_qty, comment_exist(True/False)
        client_result = {
            self.guest_client: (
                f"{reverse('users:login')}?next={self.REVERSE_ADD_COMMENT}",
                'authorized_comment',
                0,
                False
            ),
            self.authorized_client: (
                self.REVERSE_POST_DETAIL,
                'unathorized_comment',
                1,
                True
            )
        }
        for client, (redirect_url,
                     comment_text,
                     add_comment_qty,
                     comment_exist) in client_result.items():
            with self.subTest(client=client):
                form_data = {
                    'text': comment_text
                }
                response = client.post(
                    self.REVERSE_ADD_COMMENT,
                    data=form_data,
                    follow=True
                )
                # Проверяем, сработал ли редирект
                self.assertRedirects(
                    response,
                    redirect_url
                )
                # Проверяем, увеличилось ли число комментариев у поста
                self.assertEqual(
                    self.post.comments.count(),
                    comment_count + add_comment_qty
                )
                # Проверяем, создан ли комментарий с заданным текстом у поста
                self.assertEqual(
                    self.post.comments.filter(
                        text=comment_text
                    ).exists(),
                    comment_exist
                )
