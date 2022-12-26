from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from ..models import Group, Post

User = get_user_model()


class PostURLTests(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create(username='author')

        cls.post = Post.objects.create(
            text='Тестовый текст',
            author=cls.author
        )

        cls.group = Group.objects.create(
            title='тестовое название',
            slug='test-slug',
            description='тестовое описание'
        )
        cls.templates = {
            '/': 'posts/index.html',
            f'/group/{cls.group.slug}/': 'posts/group_list.html',
            f'/profile/{cls.post.author}/': 'posts/profile.html',
            f'/posts/{cls.post.pk}/': 'posts/post_detail.html',
            '/create/': 'posts/create_post.html',
            f'/posts/{cls.post.pk}/edit/': 'posts/create_post.html',
        }
        cls.INDEX_REVERSE = reverse('posts:index')
        cls.GROUP_REVERSE = reverse(
            'posts:group_posts',
            kwargs={'slug': cls.group.slug}
        )
        cls.PROFILE_REVERSE = reverse(
            'posts:profile',
            kwargs={'username': cls.post.author.get_username()}
        )
        # NB! Another version of DETAIL_REVERSE exists
        # And is called IMAGE_DETAIL_REVERSE
        cls.DETAIL_REVERSE = reverse(
            'posts:post_detail',
            kwargs={'post_id': cls.post.pk}
        )
        cls.EDIT_REVERSE = reverse(
            'posts:post_edit',
            kwargs={'post_id': cls.post.pk}
        )
        cls.CREATE_REVERSE = reverse('posts:post_create')
        cls.FOLLOW_REVERSE = reverse('posts:follow_index')

    def setUp(self):
        self.author_client = Client()
        self.authorized_client = Client()
        self.guest_client = Client()
        self.user = User.objects.create(username='AuthorizedClient')
        self.author_client.force_login(self.author)
        self.authorized_client.force_login(self.user)

    def test_correct_template_used(self):
        """Доступны ли страницы по их шаблонам"""
        for_auth = ['/create/', ]
        for_author = [f'/posts/{self.post.pk}/edit/', ]

        for address, expected_template in self.templates.items():
            with self.subTest(field=address):
                if address in for_author:
                    response = self.author_client.get(address)
                elif address in for_auth:
                    response = self.authorized_client.get(address)
                else:
                    response = self.guest_client.get(address)
                self.assertTemplateUsed(
                    response,
                    expected_template,
                    f'''
                {address} не использует шаблон {expected_template}!:{response}
                '''
                )

    def test_url(self):
        """Проверяем URLs по их реверсам"""
        pages_url = [
            (self.INDEX_REVERSE, HTTPStatus.OK, True),
            (self.GROUP_REVERSE, HTTPStatus.OK, True),
            (self.PROFILE_REVERSE, HTTPStatus.OK, True),
            (self.DETAIL_REVERSE, HTTPStatus.OK, True),
            (self.EDIT_REVERSE, HTTPStatus.FOUND, False),
            (self.CREATE_REVERSE, HTTPStatus.OK, False),
            (self.FOLLOW_REVERSE, HTTPStatus.OK, False),
            ('/unexisting_page/', HTTPStatus.NOT_FOUND, False)
        ]
        for page, answer, bool_value in pages_url:
            with self.subTest(page=page):
                if bool_value is False:
                    response = self.authorized_client.get(page)
                else:
                    response = self.guest_client.get(page)
                self.assertEqual(response.status_code, answer)
