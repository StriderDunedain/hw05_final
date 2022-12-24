from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import Client, TestCase

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
        cls.pages = {
            'main': '/',
            'group_posts': f'/group/{cls.group.slug}/',
            'profile': f'/profile/{cls.post.author}/',
            'posts': f'/posts/{cls.post.pk}/',
            'edit': f'/posts/{cls.post.pk}/edit/',
            'create': '/create/',
        }
        cls.templates = {
            '/': 'posts/index.html',
            f'/group/{cls.group.slug}/': 'posts/group_list.html',
            f'/profile/{cls.post.author}/': 'posts/profile.html',
            f'/posts/{cls.post.pk}/': 'posts/post_detail.html',
            '/create/': 'posts/create_post.html',
            f'/posts/{cls.post.pk}/edit/': 'posts/create_post.html',
        }

    def setUp(self):
        self.author_client = Client()
        self.authorized_client = Client()
        self.guest_client = Client()
        self.user = User.objects.create(username='AuthorizedClient')
        self.author_client.force_login(self.author)
        self.authorized_client.force_login(self.user)

    def test_guest_client_pages(self):
        """Доступны ли страницы по их URL"""
        for_author = ['edit', ]
        for_auth = ['create', ]
        for name, address in self.pages.items():
            with self.subTest(field=name):
                if name in for_auth:
                    response = self.authorized_client.get(address)
                elif name in for_author:
                    response = self.author_client.get(address)
                else:
                    response = self.guest_client.get(address)
                self.assertEqual(
                    response.status_code,
                    HTTPStatus.OK,
                    f'Что-то пошло не так в {address}!'
                )

    def test_non_existent_page(self):
        response = self.guest_client.get('/nonexistent/')
        self.assertEqual(
            response.status_code,
            HTTPStatus.NOT_FOUND,
            'NON-EXISTENT TROUBLES! RUUUUNN!'
        )

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
