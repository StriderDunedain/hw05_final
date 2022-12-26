from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from ..models import Group, Post

User = get_user_model()


class PostCommentsTests(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.author = User.objects.create(username='author228')

        cls.group = Group.objects.create(
            title='тестовое название',
            slug='testslug',
            description='тестовое описание',
        )

        cls.post = Post.objects.create(
            text='тестовый текст',
            author=cls.author,
            group=cls.group,
        )

        cls.LOGIN = '/auth/login/'
        cls.ADD_COMMENT_REVERSE = reverse(
            'posts:add_comment',
            kwargs={'post_id': cls.post.pk}
        )
        cls.DETAIL_REVERSE = reverse(
            'posts:post_detail',
            kwargs={'post_id': cls.post.pk}
        )
        cls.comment_form = {
            'text': cls.post.text
        }

    def setUp(self):
        self.authorized_client = Client()
        self.guest_client = Client()
        self.user = User.objects.create(username='user')
        self.authorized_client.force_login(self.user)

    def test_comments_for_authorized(self):
        """Авторизованный пользователь может оставить коммент"""
        auth_response = self.authorized_client.post(
            self.ADD_COMMENT_REVERSE,
            data=self.comment_form,
            follow=True
        )
        post_detail = self.authorized_client.get(self.DETAIL_REVERSE)
        comment = post_detail.context['comments'][0]
        self.assertEqual(auth_response.status_code, HTTPStatus.OK)
        self.assertEqual(comment.text, self.post.text)
        self.assertEqual(
            comment.author.get_username(),
            self.user.get_username()
        )

    def test_comments_for_guest(self):
        """Гость не может оставить коммент"""
        guest_response = self.guest_client.post(
            self.ADD_COMMENT_REVERSE,
            data=self.comment_form,
            follow=True
        )
        self.assertRedirects(
            guest_response,
            self.LOGIN + '?next=' + self.ADD_COMMENT_REVERSE
        )
