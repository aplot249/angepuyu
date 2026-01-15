from datetime import datetime
import json
from django.conf import settings
from django.shortcuts import get_object_or_404, get_list_or_404
from django.utils import timezone
from django.utils.timezone import localtime
from rest_framework import serializers

# 发送邮件
# from utils.tcEmail import tcEmailTypeSend
from .models import *
from django.utils.timezone import now
# from utils.wx_notice import wx_notice_send
from lxml import etree
from django.conf import settings
from myuser.serializers import UserProfileSerializer


# class OnlyCountrySerilizer(serializers.ModelSerializer):
#     def to_representation(self, instance):
#         data = super().to_representation(instance)
#         obj = NoticeBar.objects.first()
#         data['notice'] = obj.content
#         return data
#
#     class Meta:
#         model = Country
#         fields = "__all__"


class CarouselSerilizer(serializers.ModelSerializer):
    # img = serializers.ImageField(
    #     label="图片",
    #     max_length=256,  # 图片名最大长度
    #     use_url=False,  # 设为True则URL字符串值将用于输出表示。设为False则文件名字符串值将用于输出表示
    # )
    image_url = serializers.SerializerMethodField()

    def get_image_url(self, obj):
        return settings.DOMAIN + "/media/" + str(obj.img)

    class Meta:
        model = Carousel
        fields = "__all__"


class NoticeBarSerializer(serializers.ModelSerializer):
    class Meta:
        model = NoticeBar
        fields = "__all__"


class LingyuSerializer(serializers.ModelSerializer):
    def to_representation(self, instance):
        data = super().to_representation(instance)
        sublingyu = instance.sublingyu.values()
        # print([i for i in sublingyu])
        # print([i.ctitem.count() for i in instance.sublingyu.all()])
        ll = [i for i in sublingyu]
        lll = [i.ctitem.count() for i in instance.sublingyu.all()]
        for index, i in enumerate(ll):
            i['count'] = lll[index]
        # print(ll)
        data['sublingyu'] = ll  # 把他的subling挂在这里
        return data

    class Meta:
        model = Lingyu
        fields = "__all__"


class SublingyuSerializer(serializers.ModelSerializer):
    lingyu = serializers.CharField(source='lingyu.name')

    def to_representation(self, instance):
        data = super().to_representation(instance)
        dd = instance.aditem.values()
        data['aditem'] = dd
        return data

    class Meta:
        model = Sublingyu
        fields = "__all__"


class CtItemSerailizer(serializers.ModelSerializer):
    lingyuname = serializers.CharField(source='lingyu.name')

    def to_representation(self, instance):
        data = super().to_representation(instance)
        # data['portrait'] = [{"url": settings.DOMAIN + "/media/" + str(i.img)} for i in
        #                     ImgManage.objects.filter(ctitem=instance)]
        # data['fayin'] = [settings.DOMAIN + "/media/" + str(i.yin) for i in YinManage.objects.filter(ctitem=instance)]
        # data['fayin'] = settings.DOMAIN + "/media/zanwufayin.mp3"
        try:
            data['xiaohao'] = get_object_or_404(PointRule, name=data['word_or_phrase']).amount
        except:
            data['xiaohao'] = 0
        # print(data['xiaohao'])
        return data

    class Meta:
        # depth = 2
        model = CtItem
        fields = '__all__'


class FayinTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = FayinTypeModel
        fields = "__all__"


class MyFavoritAdSerializer(serializers.ModelSerializer):
    user = serializers.ReadOnlyField(source='user.username')
    ctitemid = serializers.ReadOnlyField(source='ctitem.id')
    lingyu = serializers.ReadOnlyField(source='ctitem.lingyu.id')
    ctitem_name = serializers.ReadOnlyField(source='ctitem.chinese')

    class Meta:
        model = MyFavoritAD
        fields = "__all__"


class UserCardHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = UserCardHistory
        read_only_fields = ('user', 'ctitem')
        fields = "__all__"

    def create(self, validated_data):
        print("validated_data:", validated_data)
        # UserCardHistory.objects.filter(user=validated_data['user'], ctitem=validated_data['ctitem']).delete()
        obj, created = UserCardHistory.objects.update_or_create(user=validated_data['user'],
                                                                ctitem=validated_data['ctitem'],
                                                                defaults={"action": validated_data['action']
                                                                          })
        return obj


class FeedbackSerializer(serializers.ModelSerializer):
    class Meta:
        model = Comments
        # fields = "__all__"
        exclude = ['user']


class MistakeSerializer(serializers.ModelSerializer):
    swahili = serializers.ReadOnlyField(source="ctitem.swahili")
    chinese = serializers.ReadOnlyField(source="ctitem.chinese")
    # fayin = serializers.ReadOnlyField(source="ctitem.fayin")
    # answers = serializers.CharField()
    # isGongke =
    # count = serializers.IntegerField()
    # answers = serializers.ListField(child=serializers.CharField())
    create_time = serializers.DateTimeField(format='%Y-%m-%d %H:%I', read_only=True)

    def create(self, validated_data):
        print("validated_data:", validated_data)
        obj, created = MistakeModel.objects.update_or_create(user=validated_data['user'],
                                                             ctitem=validated_data['ctitem'],
                                                             answers=validated_data['answers'], defaults={})
        return obj

    class Meta:
        model = MistakeModel
        fields = '__all__'
        read_only_fields = ('user', 'ctitem')


class MistakeListSerializer(serializers.ModelSerializer):
    ctitem = CtItemSerailizer()
    # swahili = serializers.ReadOnlyField(source="ctitem.swahili")
    # chinese = serializers.ReadOnlyField(source="ctitem.chinese")
    # fayin = serializers.ReadOnlyField(source="ctitem.fayin2")
    count = serializers.IntegerField()
    answers = serializers.ListField(child=serializers.CharField())
    create_time = serializers.DateTimeField(format='%Y-%m-%d %H:%I', read_only=True)

    class Meta:
        model = MistakeModel
        fields = '__all__'
        read_only_fields = ('user', 'ctitem')


class ListenPracticeModelSerializer(serializers.ModelSerializer):

    def create(self, validated_data):
        obj, created = ListenPracticeModel.objects.update_or_create(user=validated_data['user'],
                                                                    ctitem=validated_data['ctitem'],
                                                                    defaults={"action": validated_data['action']
                                                                              })
        return obj

    class Meta:
        model = ListenPracticeModel
        fields = '__all__'
        read_only_fields = ('user', 'ctitem')


class KnowledgeTypeSerializer(serializers.ModelSerializer):
    # author = UserProfileSerializer

    def to_representation(self, instance):
        data = super().to_representation(instance)
        # dd = instance.articles.values('title', 'type', 'author', 'cover', 'summary', 'date')
        data['articles'] = []
        return data

    class Meta:
        model = KnowledgeTypeModel
        fields = '__all__'
        depth = 2


class ArticleSerializer(serializers.ModelSerializer):
    date = serializers.DateTimeField(format='%Y-%m-%d %H:%I', read_only=True)

    class Meta:
        model = ArticleModel
        excludes = ['content']


class ArticleItemSerializer(serializers.ModelSerializer):
    date = serializers.DateTimeField(format='%Y-%m-%d %H:%I', read_only=True)

    class Meta:
        model = ArticleModel
        fields = '__all__'


class TopicTypeSerializer(serializers.ModelSerializer):
    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['list'] = []
        data['allcan'] = settings.ALLCAN
        return data

    class Meta:
        model = TopicTypeModel
        fields = '__all__'


class TopicModelSerializer(serializers.ModelSerializer):
    nickname = serializers.CharField(source='author.nickname', read_only=True)
    openid = serializers.CharField(source='author.openid', read_only=True)
    avatar = serializers.CharField(source='author.avatarUrl', read_only=True)
    create_time = serializers.DateTimeField(format='%Y-%m-%d %H:%I', read_only=True)

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['bounty'] = 20
        data['images'] = instance.toppicimg.values_list('img')
        data['comments'] = instance.comments.count()
        data['likes'] = instance.topiclikes.count()
        data['isLiked'] = instance.topiclikes.exists()
        return data

    class Meta:
        model = TopicModel
        fields = '__all__'
        read_only_fields = ['author', 'tag', 'likes', 'type', 'isTop']


class TopicCommentSerializer(serializers.ModelSerializer):
    author = UserProfileSerializer(read_only=True)
    create_time = serializers.DateTimeField(format='%Y-%m-%d %H:%I', read_only=True)

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['isSelf'] = bool(instance.author.id == data['author']['id'])
        return data

    class Meta:
        model = TopicComment
        fields = '__all__'
        read_only_fields = ['author', 'topic']
        # depth = 2


class TopicDetailSerializer(serializers.ModelSerializer):
    author = UserProfileSerializer
    comments = serializers.SerializerMethodField()
    create_time = serializers.DateTimeField(format='%Y-%m-%d %H:%I', read_only=True)

    def get_comments(self, obj):
        # obj是一个Parent实例
        children = obj.comments.all()
        return TopicCommentSerializer(children, many=True).data

    def to_representation(self, instance):
        data = super().to_representation(instance)
        # data['comments'] = instance.comments.values()
        data['images'] = instance.toppicimg.values()
        return data

    class Meta:
        model = TopicModel
        fields = '__all__'
        depth = 2  # 注意这里


class TopicImgSerializer(serializers.ModelSerializer):
    class Meta:
        model = TopicImgs
        fields = '__all__'


class TopicLikeSerializer(serializers.ModelSerializer):
    class Meta:
        model = TopicLikes
        read_only_fields = ('user',)
        fields = '__all__'
