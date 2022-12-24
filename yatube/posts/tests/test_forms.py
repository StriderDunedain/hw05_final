from django.conf import settings
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from django.test import Client, TestCase
from django.urls import reverse

from ..models import Group, Post

User = get_user_model()
REDIRECT = settings.LOGIN_URL


class PostFormTests(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.author = User.objects.create(username='author')
        cls.CREATE_REVERSE = reverse('posts:post_create')
        cls.PROFILE_REVERSE = reverse(
            'posts:profile',
            kwargs={'username': cls.author.get_username()}
        )
        cls.group = Group.objects.create(
            title='Тестовый заголовок',
            slug='test_slug',
            description='Тестовое описание'
        )

        cls.post = Post.objects.create(
            text='Тестовый заголовок поста',
            author=cls.author,
            group=cls.group
        )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.author)

    def test_post_create(self):
        """Валидная форма создает запись Post"""
        post_count = Post.objects.count()
        form_data = {
            'text': self.post.text,
            'group': self.group.pk
        }
        auth_response = self.authorized_client.post(
            self.CREATE_REVERSE,
            data=form_data,
            follow=True
        )
        self.assertRedirects(auth_response, self.PROFILE_REVERSE)
        post = Post.objects.first()
        self.assertEqual(Post.objects.count(), post_count + 1)
        self.assertEqual(post.text, self.post.text)
        self.assertEqual(post.group.pk, self.group.pk)
        self.assertEqual(post.author, self.post.author)

    def test_guest_create_redirect(self):
        """При попытке создания поста гость переходит на login"""
        form_data = {
            'text': self.post.text,
            'group': self.group.pk
        }
        guest_response = self.guest_client.post(
            self.CREATE_REVERSE,
            data=form_data,
            follow=True
        )
        self.assertRedirects(
            guest_response,
            reverse(REDIRECT) + '?next=/create/'
        )

    def test_post_edit(self):
        """Валидная форма при редактировании меняет пост"""
        posts = Post.objects.count()
        form_data = {
            'text': 'Новый тестовый текст',
            'group': self.group.pk
        }
        self.authorized_client.post(
            reverse('posts:post_edit', kwargs={'post_id': self.post.pk}),
            data=form_data,
            follow=True
        )
        old_post = self.post
        edited_post = get_object_or_404(
            Post,
            id=self.post.pk
        )
        self.assertEqual(Post.objects.count(), posts)
        self.assertEqual(old_post.pk, edited_post.pk)
        self.assertEqual(old_post.group, edited_post.group)
        self.assertNotEqual(old_post.text, edited_post.text)
