import shutil
import tempfile

from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..models import Follow, Group, Post

User = get_user_model()
POSTS_PER_PAGE = settings.POSTS_PER_PAGE
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostViewTests(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.author = User.objects.create(username='author228')
        cls.user_following = User.objects.create(
            username='user_following',
        )
        cls.user_follower = User.objects.create(
            username='user_follower',
        )

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
        cls.image_form = {
            'text': cls.post.text,
            'group': cls.group.pk,
            'image': cls.uploaded,
        }
        cls.create_form = {
            'text': cls.post.text,
            'group': cls.group.pk
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
        cls.templates = {
            cls.INDEX_REVERSE: 'posts/index.html',
            cls.GROUP_REVERSE: 'posts/group_list.html',
            cls.PROFILE_REVERSE: 'posts/profile.html',
            cls.DETAIL_REVERSE: 'posts/post_detail.html',
            cls.EDIT_REVERSE: 'posts/create_post.html',
            cls.CREATE_REVERSE: 'posts/create_post.html',
        }

    @classmethod
    def tearDownClass(self):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.authorized_client = Client()
        self.author_client = Client()
        self.guest_client = Client()
        self.user = User.objects.create(username='user')
        self.authorized_client.force_login(self.user)
        self.author_client.force_login(self.author)
        cache.clear()

    def test_view_correct_templates(self):
        """View возвращают ожидаемый HTML шаблон"""
        for view_name, template in self.templates.items():
            with self.subTest(view_name=view_name):
                if view_name == self.EDIT_REVERSE:
                    response = self.author_client.get(view_name)
                else:
                    response = self.authorized_client.get(view_name)
                self.assertTemplateUsed(
                    response,
                    template,
                    f'''
            Убедитесь, что {view_name} использует шаблон {template}!:{response}
                '''
                )

    def _test_context_method(self, response):
        """Обощенный тест для характеристик поста"""
        first_post = response.context['page_obj'][0]
        self.assertEqual(first_post.text, self.post.text)
        self.assertEqual(first_post.group, self.post.group)
        self.assertEqual(first_post.author, self.post.author)

    def test_index_view(self):
        """Шаблон index сформирован с правильным context"""
        response = self.authorized_client.get(self.INDEX_REVERSE)
        self._test_context_method(response)

    def test_group_posts_view(self):
        """Шаблон group_posts сформирован с правильным context"""
        response = self.authorized_client.get(self.GROUP_REVERSE)
        self._test_context_method(response)

    def test_profile_view(self):
        """Шаблон profile сформирован с правильным context"""
        response = self.authorized_client.get(self.PROFILE_REVERSE)
        self._test_context_method(response)

    def test_post_detail_view(self):
        """Шаблон post_detail сформирован с правильным context"""
        response = self.authorized_client.get(self.DETAIL_REVERSE)
        post_id = response.context['post'].id
        self.assertEqual(post_id, self.post.pk)

    def test_cache(self):
        """Проверяем работу кэша"""
        Post.objects.create(
            text=self.post.text,
            author=self.post.author,
            group=self.group
        )
        # Checking how many posts there are
        index_response_1 = self.authorized_client.get(self.INDEX_REVERSE)
        # Getting, checking and deleting new post
        profile_response = self.authorized_client.get(self.PROFILE_REVERSE)
        self._test_context_method(profile_response)
        new_post = profile_response.context['page_obj'][0]
        new_post.delete()
        # Checking how many posts there are after deletion - should be the same
        index_response_2 = self.authorized_client.get(self.INDEX_REVERSE)
        self.assertEqual(index_response_1.content, index_response_2.content)
        # Checking again, but clearing cache first, - should not be the same
        cache.clear()
        index_response_3 = self.authorized_client.get(self.INDEX_REVERSE)
        self.assertNotEqual(index_response_1.content, index_response_3.content)

    def test_images_anywhere(self):
        """Тест картинок"""
        create = self.author_client.post(
            self.CREATE_REVERSE,
            data=self.image_form,
            follow=True
        )
        post = Post.objects.first()
        IMAGE_DETAIL_REVERSE = reverse(
            'posts:post_detail',
            kwargs={'post_id': post.pk}
        )
        response = self.authorized_client.get(IMAGE_DETAIL_REVERSE)
        self._test_context_method(create)
        self.assertEqual(
            response.context['post'].image,
            f'posts/{self.uploaded.name}'
        )

    def test_post_create_and_edit_forms(self):
        """Тест формы для post_create и post_edit"""
        response = self.authorized_client.get(self.CREATE_REVERSE)
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
            'image': forms.fields.ImageField,
        }
        for view_reverse in (self.EDIT_REVERSE, self.CREATE_REVERSE):
            for value, expected_instance in form_fields.items():
                with self.subTest(value=value):
                    form_field = response.context['form'].fields.get(value)
                    self.assertIsInstance(
                        form_field,
                        expected_instance,
                        f'''{value} не экземпляр класса {expected_instance},
                         view={view_reverse}'''
                    )


class PaginatorViewTests(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create(username='author2')
        cls.INDEX_REVERSE = reverse('posts:index')
        # NB! Avoid making TOTAL_POSTS a number
        # dividable wholly by POSTS_PER_PAGE!
        # (because of "%" operator)
        cls.TOTAL_POSTS = 15

        cls.group = Group.objects.create(
            title='тестовое название',
            slug='testing-slug228',
            description='тестовое описание',
        )

        cls.posts_bulk = Post.objects.bulk_create(
            Post(
                text=f'Тестовый текст {i}',
                author=cls.author,
                group=cls.group
            ) for i in range(cls.TOTAL_POSTS)
        )

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.author)
        cache.clear()

    def test_10_posts_on_first_page(self):
        """Тестируем, что на первой странице 10 постов"""
        response = self.authorized_client.get(self.INDEX_REVERSE)
        self.assertEqual(
            len(response.context['page_obj']),
            POSTS_PER_PAGE,
            'На первой странице не 10 постов!'
        )

    def test_remaining_posts_on_last_page(self):
        """Тестируем, что на второй странице определенное количество постов"""
        response = self.authorized_client.get(
            self.INDEX_REVERSE + '?page=2'
        )
        last_page = len(self.posts_bulk) % POSTS_PER_PAGE
        if last_page == 0:
            raise ValueError('''TOTAL_POSTS нацело делится на POSTS_PER_PAGE!
                                Проверьте эти две переменные!''')
        self.assertEqual(
            len(response.context['page_obj']),
            last_page,
            f'''Количество постов на последней странице не {last_page}!
                Возможно, ошибка в TOTAL_POSTS'''
        )


class FollowTests(TestCase):
    class FollowViewsTest(TestCase):
        @classmethod
        def setUpClass(cls):
            super().setUpClass()
            cls.user_following = User.objects.create(
                username='user_following',
            )
            cls.user_follower = User.objects.create(
                username='user_follower',
            )
            cls.post = Post.objects.create(
                text='Подпишись на меня',
                author=cls.user_following,
            )
            cls.PROFILE_FOLLOW_REVERSE = reverse(
                'posts:profile_follow',
                kwargs={'username': cls.user_follower}
            )
            cls.PROFILE_UNFOLLOW_REVERSE = reverse(
                'posts:profile_unfollow',
                kwargs={'username': cls.user_follower.username},
            )
            cls.FOLLOW = '/follow/'

        def setUp(self):
            cache.clear()
            self.authorized_client_follower = Client()
            self.authorized_client_follower.force_login(self.user_follower)
            self.authorized_client_following = Client()
            self.authorized_client_following.force_login(self.user_following)

        def test_post_profile_follow(self):
            """Проверка подписки на пользователя"""
            count_follow = Follow.objects.count()
            self.authorized_client_follower.post(self.PROFILE_FOLLOW_REVERSE)
            follow = Follow.objects.all().latest('id')
            self.assertEqual(Follow.objects.count(), count_follow + 1)
            self.assertEqual(follow.author_id, self.user_follower.id)
            self.assertEqual(follow.user_id, self.user_following.id)

        def test_post_profile_unfollow(self):
            """Проверка отписки от пользователя"""
            Follow.objects.create(
                author=self.user_follower,
                user=self.user_following
            )
            count_follow = Follow.objects.count()
            self.authorized_client_follower.get(self.PROFILE_UNFOLLOW_REVERSE)
            self.assertEqual(Follow.objects.all().count(), count_follow - 1)

        def test_post_follow_index_follower(self):
            """Запись появляется в ленте подписчиков"""
            Follow.objects.create(
                user=self.user_follower,
                author=self.user_following
            )
            response = self.authorized_client_follower.get(self.FOLLOW)
            post_text_0 = response.context['page_obj'][0].text
            self.assertEqual(post_text_0, 'Тестовая запись для подписчиков')
            response = self.authorized_client_following.get()
            self.assertNotEqual(response, 'Тестовая запись для подписчиков')
