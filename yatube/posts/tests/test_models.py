from django.contrib.auth import get_user_model
from django.test import TestCase

from ..models import ABRIDGE_BY, Group, Post

User = get_user_model()


class PostModelTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='Тестовый слаг',
            description='Тестовое описание'
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост'
        )

    def test_models_have_correct_object_names(self):
        """Проверяем, что у моделей корректно работает __str__"""
        group_str = str(self.group)
        post_str = str(self.post)
        self.assertEqual(group_str,
                         self.group.title,
                         'Что-то не так с методом __str__ в Group!')
        self.assertEqual(post_str,
                         self.post.text[:ABRIDGE_BY],
                         'Что-то не так с методом __str__ в Post!')
