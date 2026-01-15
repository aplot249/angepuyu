from rest_framework.viewsets import GenericViewSet
from rest_framework.mixins import CreateModelMixin, DestroyModelMixin, RetrieveModelMixin, UpdateModelMixin, \
    ListModelMixin
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework import status
from utils.parsers import DecryptJSONParser, DecryptMultiPartParser

from django.shortcuts import get_object_or_404
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from rest_framework.views import APIView
from .serializers import *
from .models import *
from django.db.models import Q
from drf_multiple_model.views import ObjectMultipleModelAPIView
from drf_multiple_model.pagination import MultipleModelLimitOffsetPagination
from .pagination import MyPageNumberPagination
from rest_framework.permissions import IsAuthenticated
from myuser.authentications import JWTAuthentication
from .utils import check_content_safety

from django.conf import settings
from collections import defaultdict

from rest_framework.views import APIView  # 假设你使用 DRF，如果是纯 Django View 也可以

import json
import time
import random
from django.conf import settings
from django.http import JsonResponse, HttpResponse
from utils.huilv import convert_cny_to_tzs


# from django.http import HttpResponse

class SQview(APIView):
    def get(self, request):
        # return JsonResponse({'status': settings.SHOWSQ})
        with open(settings.BASE_DIR / 'huilv.txt', 'r', encoding='utf-8') as f:
            huillv = f.read()
        return Response({'status': settings.SHOWSQ, 'huillv': huillv})


class Huilv(APIView):
    def get(self, request):
        convert_cny_to_tzs(1)
        return Response({'status': 'ok'})


class IndexListView(ObjectMultipleModelAPIView):
    carousel = Carousel.objects.all()  # 首页轮播
    noticeBar = NoticeBar.objects.all()  # 小喇叭
    tuijianWords = CtItem.objects.filter(Q(isTuijian=True) & Q(word_or_phrase='0')).order_by('?')[:2]  # 推荐单词
    tuijianPhrases = CtItem.objects.filter(Q(isTuijian=True) & Q(word_or_phrase='1')).order_by('?')[:2]  # 推荐短语
    fayintype = FayinTypeModel.objects.all()  # 发音类型

    querylist = [
        {'queryset': carousel, 'serializer_class': CarouselSerilizer, 'label': 'carousel'},
        {'queryset': noticeBar, 'serializer_class': NoticeBarSerializer, 'label': 'noticeBar'},
        {'queryset': tuijianWords, 'serializer_class': CtItemSerailizer, 'label': 'tuijianWords', },
        {'queryset': tuijianPhrases, 'serializer_class': CtItemSerailizer, 'label': 'tuijianPhrases', },
        {'queryset': fayintype, 'serializer_class': FayinTypeSerializer, 'label': 'fayintype', },
    ]


class GetCtItem(GenericViewSet, RetrieveModelMixin, UpdateModelMixin):
    serializer_class = CtItemSerailizer
    queryset = CtItem.objects.all()
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    # parser_classes = (JSONParser, MultiPartParser, FormParser)  # 同样需要设置解析器
    parser_classes = (JSONParser, MultiPartParser, FormParser, DecryptMultiPartParser)  # 同样需要设置解析器

    # renderer_classes = [EncryptJSONRenderer]
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        if getattr(instance, '_prefetched_objects_cache', None):
            # If 'prefetch_related' has been applied to a queryset, we need to
            # forcibly invalidate the prefetch cache on the instance.
            instance._prefetched_objects_cache = {}

        # 在这里后台生成上传录音的记录
        ctitem = get_object_or_404(CtItem, id=serializer.data['id'])
        UserRecord.objects.create(user=self.request.user, ctitem=ctitem)
        return Response(serializer.data)

    def retrieve(self, request, *args, **kwargs):
        # yinpin 为空，这里是按给用户分配的录音频道，获取对应频道还没有录制的声音。
        print('str(request.user.luyinpindao)', str(request.user.luyinpindao))
        fayin = 'siyufayin' + str(request.user.luyinpindao)
        if fayin == 'siyufayin1':
            # fayin 为''或者Nnoe
            obj = CtItem.objects.filter(Q(siyufayin1__exact='') | Q(siyufayin1__isnull=True)).order_by('id').first()
        elif fayin == 'siyufayin2':
            # fayin2 为''或者Nnoe
            obj = CtItem.objects.filter(Q(siyufayin2__exact='') | Q(siyufayin2__isnull=True)).first()
        elif fayin == 'siyufayin3':
            # fayin3 为''或者Nnoe
            obj = CtItem.objects.filter(Q(siyufayin3__exact='') | Q(siyufayin3__isnull=True)).order_by('id').first()
        else:
            # fayin 为''或者Nnoe
            obj = CtItem.objects.filter(Q(siyufayin1__exact='') | Q(siyufayin1__isnull=True)).order_by('id').first()
        serializer = self.get_serializer(obj)
        return Response(serializer.data)

    # def perform_update(self, serializer):
    #     serializer.save(recorder=self.request.user)


class Relatedanswers(APIView):
    authentication_classes = (JWTAuthentication,)

    # permission_classes = (IsAuthenticated,)

    def post(self, request):
        print('reques,data', request.data)
        lingyu = request.data['lingyu']
        exclude = request.data['exclude']
        objs = CtItem.objects.filter(Q(lingyu=lingyu) & ~Q(chinese__icontains=exclude)).values_list('chinese')
        # print(objs)
        objs = [i[0] for i in objs]
        objs = random.sample(objs, 3)
        return Response({'data': objs})
        # return JsonResponse({'data': objs})


class CtiemListView(GenericViewSet, ListModelMixin):
    serializer_class = CtItemSerailizer
    pagination_class = MyPageNumberPagination
    search_fields = ('chinese', 'english', 'swahili')
    filter_backends = (SearchFilter, OrderingFilter)

    def get_queryset(self):
        print(self.request.query_params['subid'])
        wp = self.request.GET.get('wp', None)
        # 这里主要进行了分类和排序
        # 如果有子领域ID，那就是查看子领域；如果没有那就是全局搜索
        if self.request.query_params['subid'] != 'null':
            sublingyu = Sublingyu.objects.get(id=self.request.query_params['subid'])
            print(sublingyu)
            # wp是前端传来的标记，他存在一个值，用以判断是单词还是短语，如果他存在则就去取值，筛选过滤功能
            if wp:
                objs = CtItem.objects.filter(Q(lingyu=sublingyu) & Q(word_or_phrase=wp))
            else:
                objs = CtItem.objects.filter(lingyu=sublingyu)
            return objs
        else:  # 全局搜索
            objs = CtItem.objects.filter(word_or_phrase=wp)
            return objs


class CtiemByUserListView(GenericViewSet, ListModelMixin):
    serializer_class = CtItemSerailizer
    pagination_class = MyPageNumberPagination
    search_fields = ('chinese', 'english', 'swahili')
    filter_backends = (SearchFilter, OrderingFilter)
    authentication_classes = [JWTAuthentication, ]
    permission_classes = [IsAuthenticated, ]

    def get_queryset(self):
        # 根据前端保存的id数据来，后端数据库筛选
        # qq = json.loads(self.request.data['q'])
        # objs = CtItem.objects.filter(Q(id__in=qq) & Q(word_or_phrase=self.request.data['wp']))
        # return objs

        # 根据自己数据表里数据返回给前端，先从已认识和不认识的表里筛选，根据用户和不认识，拿到词条信息
        id_list = UserCardHistory.objects.filter(user=self.request.user, action='1').values_list('ctitem', flat=True)
        objs = CtItem.objects.filter(Q(id__in=id_list) & Q(word_or_phrase=self.request.data['wp']))
        return objs


class LingyuListView(GenericViewSet, ListModelMixin):
    queryset = Lingyu.objects.all()
    serializer_class = LingyuSerializer

    # 带统计数据的，每类词汇呈现
    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        data = serializer.data
        res = []
        for lingyu in data:
            sum = 0
            for sub in dict(lingyu)["sublingyu"]:
                sum = sum + sub['count']
            lingyu['sum'] = sum
            res.append(lingyu)
        return Response(res)
        # return Response(serializer.data)


# 根据词条，创建一个收藏记录
class FavouriteManage(GenericViewSet, CreateModelMixin, DestroyModelMixin):
    serializer_class = MyFavoritAdSerializer
    queryset = MyFavoritAD.objects.all()
    authentication_classes = (JWTAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get_object(self):
        id = self.request.data['ctitemid']
        obj = MyFavoritAD.objects.filter(user=self.request.user, ctitem=get_object_or_404(CtItem, id=id))
        return obj

    def perform_create(self, serializer):
        # 根据词条，创建一个收藏记录，同时再次把词条所属的子分类收藏记录，也创建了,不同步创建单词该子类下属所有单词favAllItem=False
        ctitem = get_object_or_404(CtItem, id=self.request.data['ctitem'])
        MyFavoritCat.objects.update_or_create(user=self.request.user, sublingyu=ctitem.lingyu, favAllItem=False,
                                              defaults={})
        serializer.save(user=self.request.user, ctitem=ctitem)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        # print('instance', instance)
        count = MyFavoritAD.objects.filter(ctitem__lingyu=instance[0].ctitem.lingyu).count()
        # print('count', count)
        id = instance[0].ctitem.lingyu.id
        sublingyu = instance[0].ctitem.lingyu
        self.perform_destroy(instance)
        if count == 1:
            MyFavoritCat.objects.filter(user=self.request.user, sublingyu=sublingyu).delete()
            isLast = True
        else:
            isLast = False
        # return JsonResponse({'isLast': isLast, 'id': id})
        return Response({'isLast': isLast, 'id': id})


class FeedbackView(GenericViewSet, CreateModelMixin):
    authentication_classes = (JWTAuthentication,)
    permission_classes = (IsAuthenticated,)
    serializer_class = FeedbackSerializer
    queryset = Comments.objects.all()

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class MistakeView(GenericViewSet, CreateModelMixin, ListModelMixin, UpdateModelMixin):
    queryset = MistakeModel.objects.all()
    # serializer_class = MistakeSerializer
    authentication_classes = (JWTAuthentication,)
    permission_classes = (IsAuthenticated,)
    pagination_class = MyPageNumberPagination

    def dispatch(self, request, *args, **kwargs):
        # 可以在 dispatch 方法中获取请求方法，根据不同的请求方法，响应不同的序列化类
        print(f"请求方法: {request.method}")
        if request.method == 'GET':
            self.serializer_class = MistakeListSerializer
        else:  # post、put方法
            self.serializer_class = MistakeSerializer

        return super().dispatch(request, *args, **kwargs)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user, ctitem=get_object_or_404(CtItem, id=self.request.data['ctitemid']))

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        count = MistakeModel.objects.filter(user=self.request.user).count()
        dd = serializer.data
        dd['count'] = count
        return Response(dd, status=status.HTTP_201_CREATED, headers=headers)

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset().filter(isGongke=False, user=request.user))
        # 使用字典进行分组
        grouped_dict = defaultdict(lambda: {'count': 0, 'answers': []})

        for item in queryset:
            # 这里进行了每一词条所犯的错误答案的整合
            key = (item.user, item.ctitem)
            grouped_dict[key]['id'] = item.id
            grouped_dict[key]['count'] += 1
            grouped_dict[key]['answers'].append(item.answers)

        # 转换为列表格式以便序列化
        results = []
        for (fa, fb), val in grouped_dict.items():
            results.append({
                'id': val['id'],
                'user': fa,
                'ctitem': fb,
                'count': val['count'],
                'answers': val['answers']
            })
        # print('results', results)
        page = self.paginate_queryset(results)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            dd = {}
            dd["data"] = serializer.data
            dd['yigongke'] = self.queryset.filter(isGongke=True, user=request.user).count()
            dd['weigongke'] = self.queryset.filter(isGongke=False, user=request.user).count()
            return self.get_paginated_response(dd)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class ListenRandomPractice(GenericViewSet, ListModelMixin, UpdateModelMixin):
    authentication_classes = (JWTAuthentication,)
    # permission_classes = (IsAuthenticated,)
    serializer_class = CtItemSerailizer  # 最后都是词条

    def get_permissions(self):
        # 获取请求参数
        allownologin = self.request.query_params.get('allownologin', 'false').lower()
        if allownologin == 'true':
            permission_classes = []
        else:
            permission_classes = [IsAuthenticated]
        # 返回权限类的实例列表
        return [permission() for permission in permission_classes]

    def get_queryset(self):
        if (self.request.query_params['allownologin']):
            user = get_object_or_404(UserProfile, nickname='249')
        else:
            user = self.request.user
        batch_size = 5  # 每次请求返回多少道题
        # 1. 获取所有题目的 ID (这是极轻量级的查询)
        # .values_list('id', flat=True) 返回的是一个数字列表，如 [1, 2, 3, ...]
        favadList = MyFavoritAD.objects.select_related('ctitem').filter(user=user,
                                                                        ctitem__word_or_phrase='1')  # 收藏的词条，这里只取句子，不是短语
        ctitems = [item.ctitem.id for item in favadList]  # 遍历的都是收藏夹里的词条
        all_card_ids = set(ctitems)
        print('all', all_card_ids)

        all_question_ids = set(CtItem.objects.values_list('id', flat=True))
        # 2. 获取用户已经做过的题目 ID
        wrong_item_ids = set(
            ListenPracticeModel.objects.filter(user=user, action=0).values_list('ctitem_id', flat=True)  # 已记住的词条
        )
        right_item_ids = set(
            ListenPracticeModel.objects.filter(user=user, action=1).values_list('ctitem_id', flat=True)  # 没记住的词条
        )
        print('wrong_item_ids', wrong_item_ids)
        print('right_item_ids', right_item_ids)
        # 3. 计算剩余可用的题目 ID (集合差集、并集运算，减去已记住的，加上没记住的),
        # available_ids = list((all_card_ids - right_item_ids).union(wrong_item_ids))
        available_ids = list(all_card_ids)

        # print('ava', available_ids)
        tip = False
        if len(available_ids) < 2 * batch_size:
            print(f'要提示，batch是{batch_size}', len(available_ids) - 2 * batch_size)
            tip = True
        # 5. 随机抽取 ID
        # 如果剩余题目不足 batch_size，则全取；否则随机取 batch_size 个
        count_to_fetch = min(len(available_ids), batch_size)
        selected_ids = random.sample(available_ids, count_to_fetch)
        # 6. 根据选中的 ID 获取题目详情
        # 注意：这里使用 id__in 查询，数据库效率很高
        cards_queryset = CtItem.objects.filter(id__in=selected_ids)
        return (cards_queryset, tip)

    def list(self, request, *args, **kwargs):
        if (self.request.query_params['allownologin']):
            user = get_object_or_404(UserProfile, nickname='249')
        else:
            user = self.request.user
        # queryset = self.filter_queryset(self.get_queryset())
        queryset = self.filter_queryset(self.get_queryset()[0])
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        print('serializer.data', serializer.data)
        qq = self.get_queryset()[-1]
        rightNum = ListenPracticeModel.objects.filter(user=user, action='1').count()
        wrongNum = ListenPracticeModel.objects.filter(user=user, action='0').count()
        data = {}
        if qq:
            data['tip'] = True
            data['data'] = serializer.data
            data['rightNum'] = rightNum
            data['wrongNum'] = wrongNum
            return Response(data)
        else:
            data['tip'] = False
            data['data'] = serializer.data
            data['rightNum'] = rightNum
            data['wrongNum'] = wrongNum
            return Response(data)


class ListenPracticeView(GenericViewSet, CreateModelMixin):
    authentication_classes = (JWTAuthentication,)
    permission_classes = (IsAuthenticated,)
    serializer_class = ListenPracticeModelSerializer  # 最后都是词条
    queryset = ListenPracticeModel.objects.all()

    def perform_create(self, serializer):
        ctitem = get_object_or_404(CtItem, id=self.request.data['ctitem'])
        serializer.save(user=self.request.user, ctitem=ctitem)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        data = serializer.data
        rightNum = ListenPracticeModel.objects.filter(user=request.user, action='1').count()
        wrongNum = ListenPracticeModel.objects.filter(user=request.user, action='0').count()
        data['rightNum'] = rightNum
        data['wrongNum'] = wrongNum
        headers = self.get_success_headers(data)
        return Response(data, status=status.HTTP_201_CREATED, headers=headers)


class RandomCardView(GenericViewSet, ListModelMixin):
    authentication_classes = (JWTAuthentication,)
    # permission_classes = (IsAuthenticated,)
    serializer_class = CtItemSerailizer  # 最后都是词条

    def get_permissions(self):
        # 获取请求参数
        allownologin = self.request.query_params.get('allownologin', 'false').lower()
        # 允许不登录就能获取数据
        if allownologin == 'true':
            permission_classes = []
        else:
            # 不允许不登录就能获取数据
            permission_classes = [IsAuthenticated]
        # 返回权限类的实例列表
        return [permission() for permission in permission_classes]

    def get_queryset(self):
        # 如果没有登录就分配的事249的数据
        if (self.request.query_params['allownologin']):
            user = get_object_or_404(UserProfile, nickname='249')
        else:  # 如果登录了就是用户自己的数据
            user = self.request.user
        batch_size = 5  # 每次请求返回多少道题
        # 1. 获取所有题目的 ID (这是极轻量级的查询)
        # .values_list('id', flat=True) 返回的是一个数字列表，如 [1, 2, 3, ...]
        favadList = MyFavoritAD.objects.select_related('ctitem').filter(user=user)  # 词条收藏表里查询，这个表数据量非常多！！！
        ctitems = [item.ctitem.id for item in favadList]  # 遍历的都是收藏夹里的词条对应的id
        all_card_ids = set(ctitems)
        # print('all', all_card_ids)
        # all_question_ids = set(CtItem.objects.values_list('id', flat=True))
        # 2. 获取用户已经做过的题目 ID
        rememberd_card_ids = set(
            UserCardHistory.objects.filter(user=user, action=0).select_related('ctitem').values_list('ctitem_id',
                                                                                                     flat=True)
            # 已记住的词条
        )
        not_rememberd_card_ids = set(
            UserCardHistory.objects.filter(user=user, action=1).select_related('ctitem').values_list('ctitem_id',
                                                                                                     flat=True)
            # 没记住的词条
        )
        # print('rememberd_question_ids', rememberd_card_ids)
        # print('not_rememberd_question_ids', not_rememberd_card_ids)
        # 3. 计算剩余可用的题目 ID (集合差集、并集运算，减去已记住的，加上没记住的，没记住的要反复练习),
        available_ids = list((all_card_ids - rememberd_card_ids).union(not_rememberd_card_ids))
        # print('ava', available_ids)
        tip = False
        if len(available_ids) < 2 * batch_size:
            print(f'要提示，batch是{batch_size}', len(available_ids) - 2 * batch_size)
            tip = True
        # 5. 随机抽取 ID
        # 如果剩余题目不足 batch_size，则全取；否则随机取 batch_size 个
        count_to_fetch = min(len(available_ids), batch_size)
        selected_ids = random.sample(available_ids, count_to_fetch)
        # 6. 根据选中的 ID 获取题目详情
        # 注意：这里使用 id__in 查询，数据库效率很高
        cards_queryset = CtItem.objects.filter(id__in=selected_ids)
        return (cards_queryset, tip)

    def list(self, request, *args, **kwargs):
        if (self.request.query_params['allownologin']):
            user = get_object_or_404(UserProfile, nickname='249')
        else:
            user = self.request.user
        # queryset = self.filter_queryset(self.get_queryset())
        queryset = self.filter_queryset(self.get_queryset()[0])

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        # print('serializer.data', serializer.data)
        qq = self.get_queryset()[-1]
        forgotCount = UserCardHistory.objects.filter(user=user, action='1').count()
        knownCount = UserCardHistory.objects.filter(user=user, action='0').count()
        data = {}
        if qq:
            data['tip'] = True
            data['data'] = serializer.data
            data['knownCount'] = knownCount
            data['forgotCount'] = forgotCount
            return Response(data)
        else:
            data['tip'] = False
            data['data'] = serializer.data
            data['knownCount'] = knownCount
            data['forgotCount'] = forgotCount
            return Response(data)
            # return Response(serializer.data)


class RandomQuestionView(GenericViewSet, ListModelMixin):
    authentication_classes = (JWTAuthentication,)
    # permission_classes = (IsAuthenticated,)
    serializer_class = CtItemSerailizer  # 最后是词条

    def get_permissions(self):
        # 获取请求参数
        allownologin = self.request.query_params.get('allownologin', 'false').lower()
        if allownologin == 'true':
            permission_classes = []
        else:
            permission_classes = [IsAuthenticated]
        # 返回权限类的实例列表
        return [permission() for permission in permission_classes]

    def get_queryset(self):
        if (self.request.query_params['allownologin']):
            user = get_object_or_404(UserProfile, nickname='249')
        else:
            user = self.request.user
        batch_size = 5  # 每次请求返回多少道题
        # 1. 获取所有题目的 ID (这是极轻量级的查询)
        # .values_list('id', flat=True) 返回的是一个数字列表，如 [1, 2, 3, ...]
        favadList = MyFavoritAD.objects.select_related('ctitem').filter(user=user)  # 收藏的词条，这个表里数据非常多
        ctitems = [item.ctitem.id for item in favadList]  # 遍历的都是收藏夹里的词条
        all_question_ids = set(ctitems)
        # print('all', all_question_ids)
        # all_question_ids = set(CtItem.objects.values_list('id', flat=True))
        # 2. 获取用户已经做过的题目 ID
        mistake_ids = set(
            MistakeModel.objects.filter(user=user).values_list('ctitem_id', flat=True)  # 已记住的词条
        )
        print('mistake_ids', mistake_ids)
        # 3. 计算剩余可用的题目 ID (集合差集、并集运算，减去已记住的，加上没记住的),
        # available_ids = list(mistake_ids) if len(all_question_ids) < len(mistake_ids) else list(
        #     all_question_ids - mistake_ids)
        available_ids = list(all_question_ids)
        print('ava', available_ids)
        tip = False
        if len(available_ids) < 2 * batch_size:
            print(f'要提示，batch是{batch_size}', len(available_ids) - 2 * batch_size)
            tip = True
        # 5. 随机抽取 ID
        # 如果剩余题目不足 batch_size，则全取；否则随机取 batch_size 个
        count_to_fetch = min(len(available_ids), batch_size)
        selected_ids = random.sample(available_ids, count_to_fetch)
        # 6. 根据选中的 ID 获取题目详情
        # 注意：这里使用 id__in 查询，数据库效率很高
        question_queryset = CtItem.objects.filter(id__in=selected_ids)
        return (question_queryset, tip)

    def list(self, request, *args, **kwargs):
        if (self.request.query_params['allownologin']):
            user = get_object_or_404(UserProfile, nickname='249')
        else:
            user = self.request.user
            self.permission_classes = (IsAuthenticated,)

        # queryset = self.filter_queryset(self.get_queryset())
        queryset = self.filter_queryset(self.get_queryset()[0])

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        print('serializer.data', serializer.data)
        qq = self.get_queryset()[-1]
        mistakeCount = MistakeModel.objects.filter(user=user, isGongke=False).count()
        data = {}
        if qq:
            data['tip'] = True
            data['data'] = serializer.data
            data['mistakeCount'] = mistakeCount
            return Response(data)
        else:
            data['tip'] = False
            data['data'] = serializer.data
            data['mistakeCount'] = mistakeCount
            return Response(data)
            # return Response(serializer.data)


# 这是用户做的卡片学习
class UserCardHistoryView(GenericViewSet, CreateModelMixin, UpdateModelMixin):
    authentication_classes = (JWTAuthentication,)
    permission_classes = (IsAuthenticated,)
    serializer_class = UserCardHistorySerializer
    lookup_field = 'ctitem'

    def get_queryset(self):
        return UserCardHistory.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        ctitem = CtItem.objects.get(id=self.request.data['ctitemid'])
        serializer.save(user=self.request.user, ctitem=ctitem)

    def create(self, request, *args, **kwargs):
        # 用户创建自己的学习记录数据，返回时会带上已经学会和没学会的数量统计
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        knownCount = UserCardHistory.objects.filter(user=self.request.user, action='0').count()
        forgotCount = UserCardHistory.objects.filter(user=self.request.user, action='1').count()
        dd = serializer.data
        dd['knownCount'] = knownCount
        dd['forgotCount'] = forgotCount
        return Response(dd, status=status.HTTP_201_CREATED, headers=headers)


class SubLingyuFav(APIView):
    authentication_classes = (JWTAuthentication,)
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        print('request.data', request.data)
        sublingyu = get_object_or_404(Sublingyu, id=request.data['id'])
        # 创建该子分类下属对应的词条
        MyFavoritCat.objects.update_or_create(user=request.user, sublingyu=sublingyu, favAllItem=True, defaults={})
        objs = sublingyu.ctitem.all().values_list(flat=True)
        # return JsonResponse({'res': list(objs)})
        return Response({'res': list(objs)})

    def delete(self, request):
        sublingyu = get_object_or_404(Sublingyu, id=request.data['id'])
        objs = sublingyu.ctitem.all().values_list(flat=True)
        # 批量删除下属的所有词条
        MyFavoritCat.objects.filter(user=request.user, sublingyu=sublingyu).delete()
        # return JsonResponse({'res': list(objs)})
        return Response({'res': list(objs)})


class KnowledgeTypeView(GenericViewSet, ListModelMixin):
    # authentication_classes = (JWTAuthentication,)
    # permission_classes = (IsAuthenticated,)
    serializer_class = KnowledgeTypeSerializer
    queryset = KnowledgeTypeModel.objects.all()


class KnowledgeArticlesView(GenericViewSet, ListModelMixin):
    serializer_class = ArticleItemSerializer
    pagination_class = MyPageNumberPagination

    def get_queryset(self):
        knowledgeType = get_object_or_404(KnowledgeTypeModel, id=self.request.query_params["id"])
        objs = ArticleModel.objects.filter(type=knowledgeType)
        return objs


class TopicTypeView(GenericViewSet, ListModelMixin):
    serializer_class = TopicTypeSerializer
    queryset = TopicTypeModel.objects.all()


class TopicView(GenericViewSet, ListModelMixin, CreateModelMixin, DestroyModelMixin):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = TopicModelSerializer
    pagination_class = MyPageNumberPagination

    def get_queryset(self):
        topictype = get_object_or_404(TopicTypeModel, id=self.request.query_params["id"])
        objs = TopicModel.objects.filter(type=topictype)
        return objs

    def get_object(self):
        print(self.request.data['posiId'])
        return TopicModel.objects.filter(id=self.request.data['posiId'])

    def perform_create(self, serializer):
        images = self.request.data['images']
        serializer.save(type=get_object_or_404(TopicTypeModel, name=self.request.data['type']),
                        author=self.request.user)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        # 处理images绑定
        images = request.data["images"]
        print('images', images)
        for i in images:
            TopicImgs.objects.filter(img='topicimg/' + i).update(topic=serializer.data["id"])
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)


class TopicDetailView(GenericViewSet, RetrieveModelMixin):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = TopicDetailSerializer
    queryset = TopicModel.objects.all()

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        # 增加判断是不是自己创建的
        data = serializer.data
        print('dataaaaa', data)
        data['isSelf'] = bool(data["author"]["id"] == request.user.id)
        print('selfffff', data['isSelf'])
        return Response(data)


class TopicImgView(GenericViewSet, CreateModelMixin, DestroyModelMixin):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = TopicImgSerializer
    queryset = TopicImgs.objects.all()

    def get_object(self):
        print('ggggggg', self.request.data['img'])
        obj = TopicImgs.objects.filter(img='topicimg/' + self.request.data['img'])
        return obj


class CommentView(GenericViewSet, CreateModelMixin, DestroyModelMixin):
    queryset = TopicComment.objects.all()
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = TopicCommentSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        # 在这里检查有没有违规
        openid = request.user.openid
        print('openid', openid)
        content = request.data['content']
        print('content', content)
        is_safe = check_content_safety(openid, content)
        if not is_safe:  # 违规了
            headers = self.get_success_headers(serializer.data)
            # return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
            # return JsonResponse({
            #     'code': 87014,
            #     'msg': '内容包含违规信息，请修改后重试'
            # })
            return Response({'msg': '内容包含违规信息，请修改后重试'}, status=status.HTTP_201_CREATED, headers=headers)
        else:
            self.perform_create(serializer)
            headers = self.get_success_headers(serializer.data)
            return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def perform_create(self, serializer):
        serializer.save(author=self.request.user, topic=get_object_or_404(TopicModel, id=self.request.data['topicid']))


class TopicLikeView(GenericViewSet, CreateModelMixin, DestroyModelMixin):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = TopicLikeSerializer
    queryset = TopicLikes.objects.all()

    def get_object(self):
        obj = TopicLikes.objects.filter(user=self.request.user,
                                        topic=get_object_or_404(TopicModel, id=self.request.data['topic']))
        return obj

    # def get_object(self):
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
