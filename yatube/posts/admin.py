from django.contrib import admin

from .models import Comment, Follow, Group, Post


class PostAdmin(admin.ModelAdmin):
    list_display = ('pk', 'text', 'pub_date', 'author', 'group',)
    list_editable = ('group', 'author',)
    search_fields = ('pk', 'group', 'pub_date', 'author', 'text')
    list_filter = ('group', 'pub_date', 'author',)
    empty_value_display = '-пусто-'


class GroupAdmin(admin.ModelAdmin):
    list_display = ('pk', 'title', 'slug', 'description',)
    search_fields = ('pk', 'title', 'slug',)
    list_filter = ('title', 'slug',)
    empty_value_display = '-пусто-'


class CommentAdmin(admin.ModelAdmin):
    list_display = (
        'pk',
        'text',
        'author',
        'post',
        'created',
        'edited',
    )
    search_fields = ('pk', 'author', 'created', 'edited',)
    list_filter = ('author', 'created', 'edited',)
    empty_value_display = '-пусто-'


class FollowAdmin(admin.ModelAdmin):
    list_display = ('pk', 'author', 'user',)
    search_fields = ('pk', 'author', 'user',)
    list_filter = ('author', 'user',)
    empty_value_display = '-пусто-'


admin.site.register(Post, PostAdmin)
admin.site.register(Group, GroupAdmin)
admin.site.register(Comment, CommentAdmin)
admin.site.register(Follow, FollowAdmin)
