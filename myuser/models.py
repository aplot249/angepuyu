from django.db import models

# Create your models here.
from django.contrib.auth.models import AbstractUser, UserManager
from django.core import validators
from django.db import models
from django.utils.deconstruct import deconstructible
from django.utils.translation import gettext_lazy as _
from django.forms import ModelForm, Textarea, TextInput
from django.db.models.signals import post_delete, pre_delete, pre_save
from django.dispatch import receiver


class HuiYuanType(models.Model):
    name = models.CharField(verbose_name='名称', max_length=32)
    price = models.IntegerField(verbose_name='价格数值', )
    points = models.IntegerField(verbose_name='点数', default=0)
    color = models.CharField(verbose_name='按键颜色', default='', max_length=8)
    objects = models.Manager()

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = '购买套餐'
        verbose_name_plural = verbose_name


class UserProfile(AbstractUser):
    openid = models.CharField(unique=True, max_length=200, verbose_name='openID', blank=True, null=True)
    nickname = models.CharField(max_length=64, verbose_name='微信昵称', null=True, blank=True)
    avatarUrl = models.ImageField(upload_to='portrait', verbose_name='头像', default='adminLogo.png')
    points = models.IntegerField(verbose_name='积分', default=200)
    isvip = models.BooleanField(verbose_name='是否VIP', default=False)
    totalStudyTime = models.BigIntegerField(verbose_name='学习时间/秒', default=0)
    isRecorder = models.BooleanField(verbose_name='是否可以录音', default=False)
    luyinpindao = models.CharField(verbose_name='录音频道', default='', blank=True, null=True, help_text='空、2、3',
                                   max_length=2)
    objects = UserManager()

    class Meta:
        verbose_name = '用户管理'
        verbose_name_plural = verbose_name

    def __str__(self):
        if self.nickname:
            return self.nickname
        else:
            return self.username


@receiver(pre_save, sender=UserProfile)
def avatarUrl_pre_save_handler(sender, instance, **kwargs):
    if not instance.pk:  # 新实例，没有旧文件
        return False
    try:
        old_instance = UserProfile.objects.get(pk=instance.pk)
        old_file = old_instance.avatarUrl
        # 检查文件字段是否发生了实际改变
        if old_file and old_file != instance.avatarUrl:
            old_file.delete(save=False)
    except UserProfile.DoesNotExist:
        return False


class UserLoginRecordModel(models.Model):
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='登录记录', verbose_name='用户')
    login_time = models.DateTimeField(verbose_name='登录时间', auto_now_add=True)
    login_day = models.DateField(verbose_name='登录日期', auto_now_add=True)
    objects = models.Manager()

    def __str__(self):
        return str(self.user.nickname) if str(self.user.nickname) else str(self.user.openid) + str(self.login_time)

    class Meta:
        verbose_name = '用户登录'
        verbose_name_plural = verbose_name


class ScoreRecordModel(models.Model):
    user = models.ForeignKey(UserProfile, verbose_name='用户', related_name='userscore', on_delete=models.CASCADE)
    score = models.IntegerField(verbose_name='得分')
    type = models.CharField(choices=(('0', '做题练习'), ('1', '听音组句')), default=0, verbose_name='分数类型',
                            max_length=1)
    create_time = models.DateTimeField(verbose_name='创建时间', auto_now_add=True)
    objects = models.Manager()

    class Meta:
        verbose_name = '做题得分 '
        verbose_name_plural = verbose_name


class TranscationManage(models.Model):
    user = models.ForeignKey(UserProfile, verbose_name='用户', related_name='usertranscation', on_delete=models.CASCADE)
    title = models.CharField(verbose_name='商品名称', max_length=32)
    price = models.CharField(verbose_name='价格', max_length=8)
    out_trade_no = models.CharField(verbose_name='自己系统单号', max_length=128)
    transaction_id = models.CharField(verbose_name='微信支付单号', max_length=128, default='')
    status = models.CharField(choices=(('0', '待支付'), ('1', '已支付')), verbose_name='订单状态', default='0',
                              max_length=1)
    prepay_id = models.CharField(verbose_name='微信预付订单', max_length=64, default='')
    create_time = models.DateTimeField(verbose_name='创建时间', auto_now_add=True)
    objects = models.Manager()

    class Meta:
        verbose_name = '交易管理 '
        verbose_name_plural = verbose_name

# class VoiceTpyeModel(models.Model):
#     user = models.ForeignKey(UserProfile, verbose_name='用户', related_name='uservoice', on_delete=models.CASCADE)
#     name = models.CharField(verbose_name='标记', max_length=32)
#     objects = models.Manager()
#
#     class Meta:
#         verbose_name = '声音种类 '
#         verbose_name_plural = verbose_name
