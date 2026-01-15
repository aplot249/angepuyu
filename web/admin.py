from django.contrib import admin
from .models import *
from .resource import *
from django.forms import TextInput, Textarea
from import_export.admin import ExportMixin, ImportMixin, ImportExportMixin
from import_export.formats import base_formats
# from import_export.actions import export_as_action

from django import forms
from .widget import *


# Register your models here.

@admin.register(Carousel)
class CarouselAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'img', 'index']
    list_editable = ['img', 'name', 'index']
    formfield_overrides = {
        models.CharField: {'widget': TextInput(attrs={'size': '15'})},
        # models.TextField: {'widget': Textarea(attrs={'rows': 4, 'cols': 40})},
    }

    def formfield_for_dbfield(self, db_field, request, **kwargs):
        # 判断字段名称
        if db_field.name in ['img']:
            kwargs['widget'] = portraitImageWidget
        # 对于其他字段，使用默认行为
        return super().formfield_for_dbfield(db_field, request, **kwargs)


@admin.register(NoticeBar)
class NoticebarAdmin(admin.ModelAdmin):
    list_display = ['id', 'content', 'index']
    list_editable = ['content', 'index']


@admin.register(Sublingyu)
class SublingyuAdmin(admin.ModelAdmin):
    list_display = ['id', 'index', 'name', 'lingyu', 'isTiku', 'img']
    list_filter = ['lingyu', ]
    list_editable = ['name', 'lingyu', 'index', 'isTiku', 'img']
    search_fields = ['index', 'name']
    formfield_overrides = {
        models.CharField: {'widget': TextInput(attrs={'size': '14'})},
        # models.TextField: {'widget': Textarea(attrs={'rows': 4, 'cols': 40})},
    }


class SublingyuInline(admin.TabularInline):  # 使用表格样式
    model = Sublingyu
    extra = 1  # 默认额外显示一个空白表单


@admin.register(Lingyu)
class LingyuAdmin(admin.ModelAdmin):
    formfield_overrides = {
        models.CharField: {'widget': TextInput(attrs={'size': '10'})},
        # models.TextField: {'widget': Textarea(attrs={'rows': 4, 'cols': 40})},
    }
    list_display = ['id', 'index', 'name', 'img']
    list_editable = ['index', 'name', 'index', 'img']
    inlines = [SublingyuInline, ]  # 将内联类关联到主模型

    def formfield_for_dbfield(self, db_field, request, **kwargs):
        # 判断字段名称
        if db_field.name in ['img']:
            kwargs['widget'] = portraitImageWidget
        # 对于其他字段，使用默认行为
        return super().formfield_for_dbfield(db_field, request, **kwargs)


# class ImgManageInline(admin.TabularInline):  # 使用表格样式
#     model = ImgManage
#     extra = 0  # 默认额外显示一个空白表单


@admin.register(MyFavoritAD)
class MyFavoriteAdAdmin(admin.ModelAdmin):
    list_display = ['ctitem', 'user', 'create_time']
    list_filter = ['user', ]
    autocomplete_fields = ['user']

    # def has_add_permission(self, request):
    #     return False
    #
    # def has_delete_permission(self, request, obj=None):
    #     return False
    #
    # def has_change_permission(self, request, obj=None):
    #     return False


@admin.register(MyFavoritCat)
class MyFavoriteCatAdmin(admin.ModelAdmin):
    list_display = ['sublingyu', 'user', 'create_time']
    list_filter = ['user', ]
    autocomplete_fields = ['user']

    # def has_add_permission(self, request):
    #     return False
    #
    # def has_delete_permission(self, request, obj=None):
    #     return False
    #
    # def has_change_permission(self, request, obj=None):
    #     return False


@admin.register(UserCardHistory)
class UserCardHistoryAdmin(admin.ModelAdmin):
    list_display = ['user', 'ctitem', 'action', 'created_at']


from django.db.models import Q

import threading
import requests
import time
import logging
from django.db import models, transaction, connection
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.files.base import ContentFile
from django.conf import settings

logger = logging.getLogger(__name__)


@admin.register(CtItem)
class CtItemAdmin(ImportExportMixin, admin.ModelAdmin):
    # formfield_overrides = {
    #     # models.CharField: {'widget': TextInput(attrs={'size': '10'})},
    #     models.ImageField: {'widget': portraitImageWidget},
    #     models.FileField: {'widget': mp3FileWidget}
    #     # models.TextField: {'widget': Textarea(attrs={'rows': 4, 'cols': 40})},
    # }
    resource_class = CtItemResource
    list_display = ['id', 'xuhao', 'chinese', 'english', 'swahili', 'xieyin',
                    'lingyu', "isTuijian", "word_or_phrase", 'status', 'isWrong', 'portrait',
                    'siyufayin1', 'siyufayin2', 'siyufayin3', 'generation_status', 'create_time', 'error_message']
    search_fields = ['chinese', 'english', 'swahili']
    list_filter = ('lingyu', "word_or_phrase", "status", 'isTuijian')
    list_editable = ['xuhao', 'chinese', 'xieyin', 'lingyu', 'portrait', "isTuijian", "word_or_phrase",
                     'siyufayin1', 'siyufayin2', 'siyufayin3', 'status', 'isWrong', 'swahili', 'english', 'xieyin',
                     'chinese']
    # inlines = [ImgManageInline, YinManageInline]  # 将内联类关联到主模型
    list_per_page = 100
    autocomplete_fields = ['lingyu']
    actions = ['make_published', 'siyufayin_count', 'make_record3']

    # 针对字段设置
    def formfield_for_dbfield(self, db_field, request, **kwargs):
        # 判断字段名称
        if db_field.name == 'index':
            kwargs['widget'] = forms.TextInput(attrs={'style': 'width: 60px;'})
        if db_field.name in ['chinese', 'english', 'swahili', 'xieyin']:
            kwargs['widget'] = forms.Textarea(attrs={'style': 'width: 60px;height:80px'})
        if db_field.name in ['fayin1', 'fayin2', 'fayin3']:
            kwargs['widget'] = mp3FileWidget
        if db_field.name in ['portrait']:
            kwargs['widget'] = portraitImageWidget
        # 对于其他字段，使用默认行为
        return super().formfield_for_dbfield(db_field, request, **kwargs)

    def get_export_formats(self):  # 该方法是限制格式
        formats = (
            base_formats.XLS,
        )
        return [f for f in formats if f().can_export()]

    # 1. 定义 Action 函数
    # 参数：request是请求对象，queryset是用户选中的数据集合
    @admin.action(description='批量更改状态为已发布')
    def make_published(self, request, queryset):
        rows_updated = queryset.update(status='2')
        self.message_user(request, f"{rows_updated} 词条已成功发布。")

    @admin.action(description='录音的数量')
    def siyufayin_count(self, request, queryset):
        siyufayin1_count = CtItem.objects.exclude(Q(siyufayin1__exact='') | Q(siyufayin1__isnull=True)).count()
        siyufayin2_count = CtItem.objects.exclude(Q(siyufayin2__exact='') | Q(siyufayin2__isnull=True)).count()
        siyufayin3_count = CtItem.objects.exclude(Q(siyufayin3__exact='') | Q(siyufayin3__isnull=True)).count()
        self.message_user(request,
                          f"发音1的有{siyufayin1_count}，发音2的有{siyufayin2_count}，发音3的有{siyufayin3_count}。")

    @admin.action(description='设置语音')
    def make_record3(self, request, queryset):
        for instance in queryset:
            try:
                # 更新状态为“生成中”
                instance.generation_status = 'processing'
                instance.save(update_fields=['generation_status'])

                # 2. 调用 ElevenLabs API
                url = f"https://api.elevenlabs.io/v1/text-to-speech/{settings.ELEVEN_LABS_VOICE_ID}"
                headers = {
                    "xi-api-key": settings.ELEVEN_LABS_API_KEY,
                    "Content-Type": "application/json"
                }
                # 针对斯瓦希里语的参数
                payload = {
                    "text": instance.swahili,
                    "model_id": "eleven_multilingual_v2",
                    "voice_settings": {"stability": 0.5, "similarity_boost": 0.75, "speed": 0.70, }
                }

                response = requests.post(url, json=payload, headers=headers, timeout=30)
                if response.status_code == 200:
                    # 3. 保存文件
                    tt = time.time()
                    filename = f"{tt}.mp3"
                    # save=True 会触发保存，但我们需要小心不要再次触发信号
                    # 所以我们在下面的信号里做了 check
                    instance.siyufayin3.save(filename, ContentFile(response.content), save=False)
                    instance.generation_status = 'success'
                    instance.error_message = ""
                    instance.save()
                    logger.info(f"✅ [Thread] 成功生成音频: {instance.swahili}")
                else:
                    # 4. 记录 API 报错
                    error_msg = f"API Error {response.status_code}: {response.text}"
                    instance.generation_status = 'failed'
                    instance.error_message = error_msg
                    instance.save(update_fields=['generation_status', 'error_message'])
                    logger.error(f"❌ [Thread] {error_msg}")

            except Exception as e:
                # 5. 记录代码报错 (比如网络断了)
                try:
                    # 重新获取以防万一
                    instance.generation_status = 'failed'
                    instance.error_message = str(e)
                    instance.save(update_fields=['generation_status', 'error_message'])
                except:
                    pass
                logger.error(f"❌ [Thread] 严重错误: {e}")
            finally:
                # 再次关闭连接，保持健康
                connection.close()

    # 3. 设置 Action 在页面上显示的名称
    # make_published.short_description = "批量更改状态为已发布"
    # make_published.icon = 'el-icon-check'  # ElementUI 的图标类名
    # make_published.type = 'success'  # 按钮颜色: primary, success, warning, danger, info

    # SimpleUI 独有配置：
    # enable = False  # 表示该按钮是否在只有选中数据时才可用（False则总是可用）
    # confirm = '确定要发布吗？'  # 会在点击时弹出确认框


@admin.register(FayinTypeModel)
class FayinTypeModelAdmin(admin.ModelAdmin):
    list_display = ['name', 'xuhao', 'isTuijian']
    list_editable = ['xuhao', 'isTuijian']


@admin.register(MistakeModel)
class MistakeAdmin(admin.ModelAdmin):
    list_display = ['ctitem', 'user', 'isGongke', 'answers', 'create_time']
    list_editable = ['isGongke']
    list_filter = ['user']


@admin.register(ListenPracticeModel)
class ListenPracticeAdmin(admin.ModelAdmin):
    list_display = ['user', 'ctitem', 'action']
    list_editable = ['action', ]
    list_filter = ['user']


@admin.register(PointRule)
class PointRuleAdmin(admin.ModelAdmin):
    list_display = ['name', 'amount']
    list_editable = ['amount']


@admin.register(Comments)
class CommentsAdmin(admin.ModelAdmin):
    list_display = ['user', 'content', 'create_time']

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(KnowledgeTypeModel)
class KnowledgeTypeAdmin(admin.ModelAdmin):
    list_display = ['name', ]


@admin.register(ArticleModel)
class ArticleModelAdmin(admin.ModelAdmin):
    list_display = ['title', 'type', 'author', 'cover', 'attach', 'favnum', 'date']
    list_editable = ['type', 'author']
    autocomplete_fields = ['author']


@admin.register(TopicTypeModel)
class TopicTypeAdmin(admin.ModelAdmin):
    list_display = ['name']


@admin.register(TopicModel)
class TopicAdmin(admin.ModelAdmin):
    list_display = ['id', 'title', 'type', 'author', 'tag', 'likes', 'isTop', 'create_time']
    list_editable = ['type', 'author', 'tag', 'isTop']
    list_filter = ['type', 'isTop']
    autocomplete_fields = ['author']


@admin.register(TopicImgs)
class TTopicImgsAdmin(admin.ModelAdmin):
    list_display = ['id', 'topic', 'img']
    list_editable = ['topic']


@admin.register(TopicLikes)
class TopicLikesAdmin(admin.ModelAdmin):
    list_display = ['id', 'topic', 'user']


@admin.register(TopicComment)
class TopicCommentAdmin(admin.ModelAdmin):
    list_display = ['topic', 'author', 'content', 'create_time']
    autocomplete_fields = ['author']


@admin.register(UserRecord)
class UserRecordAdmin(admin.ModelAdmin):
    list_display = ['user', 'ctitem', 'create_time']
    list_filter = ['user']
