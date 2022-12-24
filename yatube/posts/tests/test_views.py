import shutil
import tempfile

from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..models import Group, Post

User = get_user_model()
POSTS_PER_PAGE = settings.POSTS_PER_PAGE
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostViewTests(TestCase):

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
        post_count_before = Post.objects.count()
        self.authorized_client.post(
            self.CREATE_REVERSE,
            data=self.create_form,
            follow=True
        )
        self.assertNotEqual(Post.objects.count(), post_count_before)

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

    def test_3_posts_on_second_page(self):
        """Тестируем, что на второй странице 3 поста"""
        response = self.authorized_client.get(
            self.INDEX_REVERSE + '?page=2'
        )
        second_page = len(self.posts_bulk) % POSTS_PER_PAGE
        if second_page == 0:
            raise ValueError('''TOTAL_POSTS нацело делится на POSTS_PER_PAGE!
                                Проверьте эти две переменные!''')
        self.assertEqual(
            len(response.context['page_obj']),
            second_page,
            f'''Количество постов на последней странице не {second_page}!
                Возможно, ошибка в TOTAL_POSTS'''
        )
