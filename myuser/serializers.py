from django.conf import settings
from rest_framework import serializers
from web.models import MyFavoritAD, MyFavoritCat
# 发送邮件
from .models import *
from datetime import datetime


class UserProfileSerializer(serializers.ModelSerializer):
    username = serializers.CharField(read_only=True)
    password = serializers.CharField(read_only=True)
    class Meta:
        model = UserProfile
        exclude = ['user_permissions', 'groups', 'first_name', 'last_name']


    def to_representation(self, instance):
        data = super(UserProfileSerializer, self).to_representation(instance)
        if str(data['avatarUrl']).startswith('http'): #settings.DOMAIN
            data['avatarUrl'] = str(data['avatarUrl'])
        else:
            data['avatarUrl'] = str(settings.DOMAIN) + str(data['avatarUrl'])
        data['UID'] = str(datetime.now().year) + str(data['id']).zfill(3)
        data['favorites'] = [i["ctitem_id"] for i in MyFavoritAD.objects.filter(user=instance).values('ctitem_id')]
        data['favcat'] = MyFavoritCat.objects.filter(user=instance).values_list('sublingyu_id', flat=True)
        return data


class TranscationManageSerializer(serializers.ModelSerializer):
    class Meta:
        model = TranscationManage
        fields = "__all__"


class HuiYuanTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = HuiYuanType
        fields = "__all__"


class ScoreRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = ScoreRecordModel
        read_only_fields = ('user', 'create_time')
        fields = "__all__"


# class VoiceTpyeSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = ScoreRecordModel
#         read_only_fields = ('user',)
#         fields = "__all__"
