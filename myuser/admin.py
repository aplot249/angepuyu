from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.models import User, Group
from .models import *
from django import forms
from django.forms import TextInput, Textarea, EmailInput
from django.db import models

admin.site.site_header = '坦坦斯语-后台管理'
admin.site.site_title = '坦坦斯语-后台管理'
admin.site.index_title = u'坦坦斯语-后台管理'


@admin.register(HuiYuanType)
class HuiYuanTypeAdmin(admin.ModelAdmin):
    list_display = ['name', 'price', 'points', 'color']
    list_editable = ['price', 'points', 'color']


@admin.register(UserProfile)
class UserProfileAdmin(UserAdmin):
    list_display = ['id', 'openid', 'nickname', 'points', 'isvip', 'totalStudyTime', 'isRecorder', 'luyinpindao',
                    'image_data']
    list_editable = ['nickname', 'points', 'isvip', 'isRecorder', 'luyinpindao']
    # search_fields = ['nickname', 'isRecorder', 'luyinpindao']
    list_filter = ['isRecorder', 'luyinpindao', 'isvip']
    formfield_overrides = {
        models.CharField: {'widget': TextInput(attrs={'size': '14'})},
        # models.ImageField: {'widget': portraitImageWidget},
        # models.FileField: {'widget': mp3FileWidget}
        # models.TextField: {'widget': Textarea(attrs={'rows': 4, 'cols': 40})},
    }

    search_fields = ['id', 'openid', 'nickname']

    @admin.display(description='头像')
    def image_data(self, obj):
        # print(obj.avatarUrl)
        if obj.avatarUrl:
            img = '/media/' + str(obj.avatarUrl)
            return format_html(
                '<img src="{}" width="50px" height="50px"/>',
                img,
            )
        else:
            return '无'

    image_data.short_description = '头像'


@admin.register(UserLoginRecordModel)
class UserLoginRecordAdmin(admin.ModelAdmin):
    list_display = ['user', 'login_day', 'login_time']
    list_filter = ['login_day']


@admin.register(TranscationManage)
class TranscationManageAdmin(admin.ModelAdmin):
    list_display = ['title', 'user', 'price', 'out_trade_no', 'transaction_id', 'status', 'prepay_id',
                    'create_time']
    list_filter = ['title', 'user', 'status']
    autocomplete_fields = ['user']

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(ScoreRecordModel)
class ScoreRecordAdmin(admin.ModelAdmin):
    list_display = ['user', 'score', 'type', 'create_time']
    autocomplete_fields = ['user']


