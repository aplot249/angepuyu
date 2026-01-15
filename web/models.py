from django.db import models
from myuser.models import UserProfile
from django.db.models.signals import post_delete, pre_delete, pre_save, post_save
from django.dispatch import receiver
from ckeditor_uploader.fields import RichTextUploadingField

import pathlib
from django.conf import settings


# 封面轮播
class Carousel(models.Model):
    name = models.CharField(verbose_name='名称', max_length=32)
    type = models.CharField(verbose_name='标志', max_length=32, default='')
    img = models.ImageField(verbose_name='图片', upload_to='swiper')
    index = models.IntegerField(verbose_name='序号', default=0)
    objects = models.Manager()

    class Meta:
        ordering = ['index']
        verbose_name = '封面轮播'
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.name


@receiver(pre_save, sender=Carousel)
def img_pre_save_handler(sender, instance, **kwargs):
    if not instance.pk:  # 新实例，没有旧文件
        return False

    try:
        old_instance = Carousel.objects.get(pk=instance.pk)
        old_file = old_instance.img
        # 检查文件字段是否发生了实际改变
        if old_file and old_file != instance.img:
            old_file.delete(save=False)
    except Carousel.DoesNotExist:
        return False


# 喇叭通知
class NoticeBar(models.Model):
    content = models.CharField(verbose_name='内容', max_length=64)
    index = models.IntegerField(verbose_name='序号', default=0)
    objects = models.Manager()

    class Meta:
        ordering = ['index']
        verbose_name = '喇叭公告'
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.content


# 领域范围，区分是属于哪个国家的领域
class Lingyu(models.Model):
    name = models.CharField(verbose_name='领域名称', max_length=32)
    img = models.ImageField(verbose_name='图标', upload_to='lingyulogo', blank=True, null=True)
    index = models.CharField(verbose_name='序号', default=0, max_length=8)
    objects = models.Manager()

    class Meta:
        verbose_name = '领域范围'
        verbose_name_plural = verbose_name
        ordering = ['index']

    def __str__(self):
        return self.name


@receiver(pre_save, sender=Lingyu)
def img_pre_save_handler(sender, instance, **kwargs):
    if not instance.pk:  # 新实例，没有旧文件
        return False

    try:
        old_instance = Lingyu.objects.get(pk=instance.pk)
        old_file = old_instance.img
        # 检查文件字段是否发生了实际改变
        if old_file and old_file != instance.img:
            old_file.delete(save=False)
    except Lingyu.DoesNotExist:
        return False


# 区分是属于哪个大领域下的子领域
class Sublingyu(models.Model):
    name = models.CharField(verbose_name='子领域名称', max_length=64)
    lingyu = models.ForeignKey(Lingyu, on_delete=models.CASCADE, verbose_name='所属主领域', related_name='sublingyu')
    img = models.ImageField(verbose_name='图标', upload_to='subolingyulogo', blank=True, null=True)
    index = models.CharField(verbose_name='序号', default=0, max_length=8)
    isTiku = models.BooleanField(verbose_name='初始题库', default=False)
    objects = models.Manager()

    class Meta:
        verbose_name = '子领域范围'
        verbose_name_plural = verbose_name
        ordering = ['index']

    def __str__(self):
        return self.name


@receiver(pre_save, sender=Sublingyu)
def img_pre_save_handler(sender, instance, **kwargs):
    if not instance.pk:  # 新实例，没有旧文件
        return False

    try:
        old_instance = Sublingyu.objects.get(pk=instance.pk)
        old_file = old_instance.img
        # 检查文件字段是否发生了实际改变
        if old_file and old_file != instance.img:
            old_file.delete(save=False)
    except Sublingyu.DoesNotExist:
        return False


class FayinTypeModel(models.Model):
    name = models.CharField(verbose_name='类型', max_length=16)
    xuhao = models.CharField(verbose_name='标识', max_length=8, default='', blank=True, null=True)
    isTuijian = models.BooleanField(verbose_name='发音优先推荐', default=False)
    objects = models.Manager()

    class Meta:
        verbose_name = '发音种类'
        verbose_name_plural = verbose_name


# import threading
# import requests
# import time
# import logging
# from django.db import models, transaction, connection
# from django.db.models.signals import post_save
# from django.dispatch import receiver
# from django.core.files.base import ContentFile
# from django.conf import settings
#
# logger = logging.getLogger(__name__)


# 词条，属于哪个子领域下，和他的作者是谁
class CtItem(models.Model):
    lingyu = models.ForeignKey(Sublingyu, on_delete=models.CASCADE, verbose_name='所属领域', related_name='ctitem',
                               null=True, blank=True)
    xuhao = models.IntegerField(verbose_name='编号', default=0)
    chinese = models.CharField(verbose_name='汉语', max_length=64)
    english = models.CharField(verbose_name='英语', max_length=64)
    swahili = models.CharField(verbose_name='斯语', max_length=64)
    xieyin = models.CharField(verbose_name='汉语谐音', max_length=64)
    portrait = models.ImageField(verbose_name='图片', upload_to='ctportrait', null=True, blank=True,
                                 default='ctportrait/zhanwei.jpg',
                                 max_length=256)
    siyufayin1 = models.FileField(verbose_name='发音1', blank=True, null=True, upload_to='ctyinpin', default=None)
    siyufayin2 = models.FileField(verbose_name='发音2', blank=True, null=True, upload_to='ctyinpin2', default=None)
    siyufayin3 = models.FileField(verbose_name='发音3', blank=True, null=True, upload_to='ctyinpin3', default=None)
    word_or_phrase = models.CharField(verbose_name='单词还是短语', choices=(('0', '单词'), ('1', '短语')), max_length=1,
                                      default='')
    status = models.CharField(verbose_name='状态', choices=(('0', '初始draft'), ('1', '未发布'), ('2', '已发布')),
                              default='0', max_length=1)
    isTuijian = models.BooleanField(verbose_name='是否推荐', default=False)
    isWrong = models.BooleanField(verbose_name='反馈有错', default=False)
    recorder = models.ForeignKey(UserProfile, on_delete=models.CASCADE, verbose_name='录制人', blank=True, null=True)
    create_time = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    STATUS_CHOICES = [
        ('pending', '等待生成'),
        ('processing', '生成中'),
        ('success', '成功'),
        ('failed', '失败'),
    ]
    generation_status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name="生成状态"
    )
    error_message = models.TextField(blank=True, verbose_name="错误日志")
    objects = models.Manager()

    class Meta:
        ordering = ['lingyu__index', 'id']  # 根据时间从早到晚进行排序
        verbose_name = '词条信息'
        verbose_name_plural = verbose_name

    def __str__(self):
        return f"{self.chinese}-{self.english}-{self.swahili}"


# def _generate_audio_task(word_id):
#     """
#     这个函数会在后台线程中运行，完全不阻塞主页面
#     """
#     # 1. 重新获取对象（必须在线程里重新查库，不能直接传 instance）
#     try:
#         # 必须显式关闭旧连接，防止多线程数据库连接泄漏
#         connection.close()
#
#         instance = CtItem.objects.get(id=word_id)
#
#         # 更新状态为“生成中”
#         instance.generation_status = 'processing'
#         instance.save(update_fields=['generation_status'])
#
#         # 2. 调用 ElevenLabs API
#         url = f"https://api.elevenlabs.io/v1/text-to-speech/{settings.ELEVEN_LABS_VOICE_ID}"
#         headers = {
#             "xi-api-key": settings.ELEVEN_LABS_API_KEY,
#             "Content-Type": "application/json"
#         }
#         # 针对斯瓦希里语的参数
#         payload = {
#             "text": instance.swahili,
#             "model_id": "eleven_multilingual_v2",
#             "speed": "0.60",
#             "voice_settings": {"stability": 0.5, "similarity_boost": 0.75}
#         }
#
#         response = requests.post(url, json=payload, headers=headers, timeout=30)
#         if response.status_code == 200:
#             # 3. 保存文件
#             tt = time.time()
#             filename = f"{tt}.mp3"
#             # save=True 会触发保存，但我们需要小心不要再次触发信号
#             # 所以我们在下面的信号里做了 check
#             instance.siyufayin3.save(filename, ContentFile(response.content), save=False)
#             instance.generation_status = 'success'
#             instance.error_message = ""
#             instance.save()
#             logger.info(f"✅ [Thread] 成功生成音频: {instance.swahili}")
#         else:
#             # 4. 记录 API 报错
#             error_msg = f"API Error {response.status_code}: {response.text}"
#             instance.generation_status = 'failed'
#             instance.error_message = error_msg
#             instance.save(update_fields=['generation_status', 'error_message'])
#             logger.error(f"❌ [Thread] {error_msg}")
#
#     except Exception as e:
#         # 5. 记录代码报错 (比如网络断了)
#         try:
#             # 重新获取以防万一
#             instance = CtItem.objects.get(id=word_id)
#             instance.generation_status = 'failed'
#             instance.error_message = str(e)
#             instance.save(update_fields=['generation_status', 'error_message'])
#         except:
#             pass
#         logger.error(f"❌ [Thread] 严重错误: {e}")
#     finally:
#         # 再次关闭连接，保持健康
#         connection.close()


# ================= 信号触发器 =================
# @receiver(post_save, sender=CtItem)
# def trigger_audio_generation(sender, instance, created, **kwargs):
#     """
#     当 Admin 点击保存时触发
#     """
    # print('instance.siyufayin3:', instance.siyufayin3)
    # 只有在 (1) 新创建 或者 (2) 状态是 pending 且没有音频时 才触发
    # if (instance.generation_status == 'pending') and instance.siyufayin3 == '':
        # 🌟 关键点：transaction.on_commit
        # 只有当数据库事务完全提交（确认数据已写入硬盘）后，才启动线程。
        # 否则线程跑得太快，去查库时发现 ID 还不存在，会报错。
        # transaction.on_commit(lambda: threading.Thread(
        #     target=_generate_audio_task,
        #     args=(instance.id,)
        # ).start())


@receiver(pre_save, sender=CtItem)
def portrait_pre_save_handler(sender, instance, **kwargs):
    if not instance.pk:  # 新实例，没有旧文件
        return False

    try:
        old_instance = CtItem.objects.get(pk=instance.pk)
        old_file = old_instance.portrait
        # 检查文件字段是否发生了实际改变
        if old_file and old_file != instance.portrait:
            old_file.delete(save=False)
    except CtItem.DoesNotExist:
        return False


# 一次词条多次录音，删除之前已过时的
@receiver(pre_save, sender=CtItem)
def yinpin_pre_save_handler(sender, instance, **kwargs):
    if not instance.pk:  # 新实例，没有旧文件
        return False
    try:
        old_instance = CtItem.objects.get(pk=instance.pk)
        old_file = old_instance.siyufayin1
        old_file2 = old_instance.siyufayin2
        old_file3 = old_instance.siyufayin3
        # 检查文件字段是否发生了实际改变
        if old_file and old_file != instance.siyufayin1:
            old_file.delete(save=False)
        if old_file2 and old_file2 != instance.siyufayin2:
            old_file2.delete(save=False)
        if old_file3 and old_file3 != instance.siyufayin3:
            old_file3.delete(save=False)
    except CtItem.DoesNotExist:
        return False


# 单个词条收藏
class MyFavoritAD(models.Model):
    user = models.ForeignKey(UserProfile, verbose_name='用户', related_name='myfavoritad', on_delete=models.CASCADE,
                             db_index=True)
    ctitem = models.ForeignKey(CtItem, verbose_name='条目', on_delete=models.CASCADE)
    create_time = models.DateTimeField(verbose_name='创建时间', auto_now=True)
    objects = models.Manager()

    class Meta:
        verbose_name = '词条收藏'
        verbose_name_plural = verbose_name
        indexes = [
            # 1. 为 user 创建单列索引，并自定义索引名称
            models.Index(fields=['user'], name='user'),
            models.Index(fields=['ctitem'], name='ctitem'),
        ]


# 根据子领域分类的收藏，新建和删除词条
class MyFavoritCat(models.Model):
    user = models.ForeignKey(UserProfile, verbose_name='用户', related_name='myfavoritcat', on_delete=models.CASCADE)
    sublingyu = models.ForeignKey(Sublingyu, verbose_name='子领域', on_delete=models.CASCADE)
    favAllItem = models.BooleanField(verbose_name='收藏子类全部词条', default=False)
    create_time = models.DateTimeField(verbose_name='创建时间', auto_now_add=True)
    objects = models.Manager()

    class Meta:
        verbose_name = '子领域收藏'
        verbose_name_plural = verbose_name


@receiver(post_save, sender=MyFavoritCat)
def save_myFavoritCat(sender, instance, **kwargs):
    if instance.favAllItem:
        # print(instance.user)
        data = instance.sublingyu.ctitem.all()
        print('data', data)
        # objs = [MyFavoritAD(user=instance.user, ctitem=i) for i in data]
        # MyFavoritAD.objects.bulk_create(objs, update_conflicts=True, update_fields=['zz'],
        #                                 unique_fields=['user', 'ctitem'])
        # MyFavoritAD.objects.update_or_create(user=instance.user, ctitem=instance.,defaults={})
        [MyFavoritAD.objects.update_or_create(user=instance.user, ctitem=i, defaults={}) for i in data]
    else:
        pass


@receiver(pre_delete, sender=MyFavoritCat)
def delete_myFavoritCat(sender, instance, **kwargs):
    MyFavoritAD.objects.filter(ctitem__lingyu=instance.sublingyu, user=instance.user).delete()


# 用户意见反馈
class Comments(models.Model):
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='usercomments', verbose_name='用户')
    content = models.TextField(verbose_name='内容')
    create_time = models.DateTimeField(verbose_name='创建时间', auto_now_add=True)
    objects = models.Manager()

    def __str__(self):
        return self.content[:20]

    class Meta:
        verbose_name = '用户反馈 '
        verbose_name_plural = verbose_name


# 点数规则
class PointRule(models.Model):
    name = models.CharField(choices=(('0', '单词'), ('1', '短语')), verbose_name='类型', max_length=1)
    amount = models.IntegerField(verbose_name='消耗点数')
    objects = models.Manager()

    class Meta:
        verbose_name = '点数消耗 '
        verbose_name_plural = verbose_name


# 用户做题练习
class UserCardHistory(models.Model):
    """用户刷题记录表 (用于去重)"""
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE, db_index=True)
    ctitem = models.ForeignKey(CtItem, on_delete=models.CASCADE)
    action = models.CharField(choices=(('0', '认识'), ('1', '不认识')), max_length=1, verbose_name='是否记住',
                              blank=True, null=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    objects = models.Manager()

    class Meta:
        # 联合索引，加快查询速度
        verbose_name = '做过的题'
        verbose_name_plural = verbose_name
        unique_together = ('user', 'ctitem', 'action')
        indexes = [
            models.Index(fields=['user', 'ctitem', 'action']),
        ]


# 做题做错的，错题本
class MistakeModel(models.Model):
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='mistakes', verbose_name='用户',
                             db_index=True)
    ctitem = models.ForeignKey(CtItem, on_delete=models.CASCADE, verbose_name='词条')
    answers = models.CharField(verbose_name='错误答案', max_length=64)
    isGongke = models.BooleanField(verbose_name='是否攻克', default=False)
    create_time = models.DateTimeField(verbose_name='创建时间', auto_now_add=True)
    objects = models.Manager()

    class Meta:
        ordering = ["-create_time"]
        # 联合索引，加快查询速度
        verbose_name = '用户错题'
        verbose_name_plural = verbose_name


# 听音组句练习记录
class ListenPracticeModel(models.Model):
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='listenpractice', verbose_name='用户')
    ctitem = models.ForeignKey(CtItem, on_delete=models.CASCADE, verbose_name='词条')
    action = models.CharField(choices=(('0', '做错'), ('1', '做对')), max_length=1, verbose_name='正确与否',
                              blank=True, null=True)
    create_time = models.DateTimeField(verbose_name='创建时间', auto_now_add=True)
    objects = models.Manager()

    class Meta:
        ordering = ["-create_time"]
        # 联合索引，加快查询速度
        verbose_name = '听音练习记录'
        verbose_name_plural = verbose_name


class KnowledgeTypeModel(models.Model):
    name = models.CharField(verbose_name='分类名称', max_length=32)
    xuhao = models.IntegerField(verbose_name='序号')
    objects = models.Manager()

    def __str__(self):
        return self.name

    class Meta:
        # 联合索引，加快查询速度
        verbose_name = '知识分类'
        verbose_name_plural = verbose_name


class ArticleModel(models.Model):
    title = models.CharField(verbose_name='标题', max_length=64)
    author = models.ForeignKey(UserProfile, verbose_name='作者', blank=True, null=True, on_delete=models.CASCADE)
    type = models.ForeignKey(KnowledgeTypeModel, on_delete=models.CASCADE, related_name='articles')
    cover = models.ImageField(verbose_name='封面图', upload_to='article')
    summary = models.CharField(verbose_name='概述', max_length=128)
    content = RichTextUploadingField(verbose_name='内容')
    attach = models.FileField(verbose_name='附件文档', blank=True, null=True)
    favnum = models.IntegerField(verbose_name='收藏数', default=0)
    date = models.DateTimeField(verbose_name='创建时间', auto_now_add=True)
    objects = models.Manager()

    def get_cover(self):
        return settings.DOMAIN + '/' + self.cover

    def __str__(self):
        return self.title

    class Meta:
        # 联合索引，加快查询速度
        verbose_name = '知识文案'
        verbose_name_plural = verbose_name


class TopicTypeModel(models.Model):
    name = models.CharField(verbose_name='话题', max_length=32)
    objects = models.Manager()

    def __str__(self):
        return self.name

    class Meta:
        # 联合索引，加快查询速度
        verbose_name = '话题分类'
        verbose_name_plural = verbose_name


class TopicModel(models.Model):
    author = models.ForeignKey(UserProfile, verbose_name='发帖人', related_name='usertopic',
                               on_delete=models.CASCADE)
    title = models.CharField(verbose_name='标题', max_length=64, default='', blank=True, null=True)
    content = models.TextField(verbose_name='评论内容')
    type = models.ForeignKey(TopicTypeModel, related_name='typetopic', verbose_name='话题',
                             on_delete=models.CASCADE)
    create_time = models.DateTimeField(verbose_name='创建时间', auto_now_add=True)
    tag = models.CharField(verbose_name='tag标签', default='', max_length=32, blank=True, null=True)
    likes = models.IntegerField(verbose_name='点赞数', default=0)
    isTop = models.BooleanField(verbose_name='是否置顶', default=False)
    objects = models.Manager()

    def __str__(self):
        return self.content

    class Meta:
        ordering = ['-isTop', 'create_time']
        # 联合索引，加快查询速度
        verbose_name = '社区话题'
        verbose_name_plural = verbose_name


@receiver(pre_delete, sender=TopicModel)
def delete_topicImg(sender, instance, **kwargs):
    # print('instance', instance)
    # print('instance111111111', instance.toppicimg.all())
    imgs = instance.toppicimg.all()
    for ii in imgs:
        file_path = settings.BASE_DIR / 'media' / str(ii.img)
        print('file_path', file_path)
        file = pathlib.Path(file_path)  # 使用Path将文件路径转换为Path对象
        try:
            file.unlink()  # 删除文件
            print("文件删除成功！")
        except:
            print('文件不存在')


class TopicImgs(models.Model):
    topic = models.ForeignKey(TopicModel, verbose_name='话题', on_delete=models.CASCADE, related_name='toppicimg',
                              blank=True, null=True)
    img = models.ImageField(verbose_name='图片', upload_to='topicimg')
    objects = models.Manager()

    class Meta:
        # 联合索引，加快查询速度
        verbose_name = '话题图片'
        verbose_name_plural = verbose_name


class TopicLikes(models.Model):
    topic = models.ForeignKey(TopicModel, verbose_name='话题', on_delete=models.CASCADE, related_name='topiclikes')
    user = models.ForeignKey(UserProfile, verbose_name='用户', related_name='userlikes', on_delete=models.CASCADE)
    objects = models.Manager()

    class Meta:
        # 联合索引，加快查询速度
        verbose_name = '话题喜欢'
        verbose_name_plural = verbose_name


class TopicComment(models.Model):
    topic = models.ForeignKey(TopicModel, on_delete=models.CASCADE, related_name='comments', verbose_name='话题')
    author = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='authorcomments',
                               verbose_name='评论人')
    content = models.CharField(verbose_name='评论', max_length=64)
    create_time = models.DateTimeField(verbose_name='创建时间', auto_now_add=True)
    objects = models.Manager()

    def __str__(self):
        return self.content[:10]

    class Meta:
        # 联合索引，加快查询速度
        verbose_name = '话题评论'
        verbose_name_plural = verbose_name


class UserRecord(models.Model):
    user = models.ForeignKey(UserProfile, verbose_name='录制人', on_delete=models.CASCADE)
    ctitem = models.ForeignKey(CtItem, verbose_name='词条', on_delete=models.CASCADE)
    create_time = models.DateTimeField(verbose_name='录制时间', auto_now_add=True)
    objects = models.Manager()

    class Meta:
        # 联合索引，加快查询速度
        verbose_name = '录制记录'
        verbose_name_plural = verbose_name
