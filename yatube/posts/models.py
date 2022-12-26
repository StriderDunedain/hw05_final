from django.contrib.auth import get_user_model
from django.db import models

User = get_user_model()
ABRIDGE_BY = 35


class Group(models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=30, unique=True)
    description = models.TextField()

    def __str__(self):
        return self.title


class Post(models.Model):
    text = models.TextField(
        'Текст поста',
        help_text='Введите текст нового поста',
    )
    pub_date = models.DateTimeField(auto_now_add=True)
    header = models.CharField(
        'Заголовок',
        help_text='Введите заголовок (опционально)',
        blank=True,
        max_length=50
    )
    edited = models.DateTimeField(blank=True, null=True)
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='posts'
    )
    group = models.ForeignKey(
        Group,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='posts',
        verbose_name='Группа',
        help_text='Выберите группу (опционально)'
    )
    image = models.ImageField(
        'Картинка',
        upload_to='posts/',
        blank=True
    )

    class Meta:
        ordering = ('-pub_date',)
        verbose_name = 'Пост'
        verbose_name_plural = 'Посты'

    def __str__(self):
        return self.text[:ABRIDGE_BY]


class Comment(models.Model):
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        related_name='comments'
    )
    created = models.DateTimeField(auto_now_add=True)
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='comments'
    )
    text = models.TextField(
        help_text='Комментарий ждет...'
    )
    edited = models.DateTimeField(blank=True, null=True)

    class Meta:
        ordering = ('-created',)


class Follow(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='follower'
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='following'
    )

    class Meta:
        models.UniqueConstraint(
            fields=['user', 'author'],
            name='follow_together_constraint'
        )
