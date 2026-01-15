"""tongchengQyApi URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.urls import re_path, path

from .views import *

urlpatterns = [
    path('sq/', SQview.as_view()),  # 首页是否显示社区入口的，返回的事setting里设置的SHOWSQ
    path('huilv/', Huilv.as_view()),  # 首页是否显示社区入口的，返回的事setting里设置的SHOWSQ
    path("index/", IndexListView.as_view()),  # 首页轮播图、小喇叭、推荐、发音type类型内容

    path("lingyu/", LingyuListView.as_view({'get': 'list'})),  # 分类页面主和子领域

    # 用户在词库分类页面点击，进入list客观页面，所有用户看到的都一样，根据子领域ID，查看归属他的单词、短语2类【全部呈现】
    re_path("ctiemBySub/$", CtiemListView.as_view({'get': 'list'})),

    path('sublingyufav/', SubLingyuFav.as_view()),  # 对每个子分类，进行收藏操作，新建或者取消收藏，进行批量管理词条

    # 在list客观页面，用户对 子分类下属单个词条，进行创建收藏的操作，
    path("favourite/", FavouriteManage.as_view({'post': 'create'})),
    # 在list客观页面，用户对子分类下属 单个词条 进行删除收藏的操作，
    path("delfavourite/", FavouriteManage.as_view({'delete': 'destroy'})),

    re_path("ctiemByFav/$", CtiemByUserListView.as_view({'post': 'list'})),  # 我的生词本页面，根据用户收藏，查看用户收藏的所有单词、短语【综合呈现用户收藏】

    re_path("^getctitem/$", GetCtItem.as_view({'get': 'retrieve'})),  # 词条条目，用于录音，每次取一条
    re_path("^updatectitem/(?P<pk>.*)/$", GetCtItem.as_view({'post': 'partial_update'})),  # 条目，录音贡献逻辑上传录音

    path('randomcard/', RandomCardView.as_view({'get': 'list'})),  # 随机取出卡片，请求数据，从我收藏的词条里取数据
    path('updateusercard/', UserCardHistoryView.as_view({'post': 'create'})),  # 更新用户卡片学习的卡片状态，
    re_path('updateusercard/(?P<ctitem>.*)/', UserCardHistoryView.as_view({'put': 'partial_update'})),  # 更新用户卡片学习的卡片状态，

    path('randomquestion/', RandomQuestionView.as_view({'get': 'list'})),  # 随机取出做题，请求数据，从我收藏的词条里取数据
    path("relatedanswers/", Relatedanswers.as_view()),  # 做题拿到相关答案

    path('mistake/', MistakeView.as_view({'post': 'create', 'get': 'list'})),  # 做错的题目
    re_path('mistake/(?P<pk>.*)/', MistakeView.as_view({'put': 'partial_update'})),  # 更新做错的题目

    path('listenpractice/', ListenRandomPractice.as_view({'get': 'list'})),  # 做错的题目
    path('listenpracticeupdate/', ListenPracticeView.as_view({'post': 'create'})),  # 记录听音组词的数据

    path('knowledgetype/', KnowledgeTypeView.as_view({'get': 'list'})),  # 知识库分类，暂时没用
    path('knowledgearticles/', KnowledgeArticlesView.as_view({'get': 'list'})),  # 知识库分类对应文章，暂时没用

    path('topictype/', TopicTypeView.as_view({'get': 'list'})),  # 话题，对应的分类
    path('topic/', TopicView.as_view({'get': 'list', 'post': 'create'})),  # 话题的创建操作
    re_path('topic/(?P<pk>.*?)/', TopicView.as_view({'delete': 'destroy'})),  # 话题的删除
    re_path('topicdetail/(?P<pk>.*)/', TopicDetailView.as_view({'get': 'retrieve'})),  # 话题详情的查看
    path('topiclike/', TopicLikeView.as_view({'post': 'create', 'delete': 'destroy'})),  # 话题点赞
    path('topicimg/', TopicImgView.as_view({'post': 'create', "delete": 'destroy'})),  # 话题图片
    path('topiccomment/', CommentView.as_view({'post': 'create'})),  # 话题评论的创建
    re_path('topiccomment/(?P<pk>.*?)/', CommentView.as_view({"delete": 'destroy'})),  # 话题评论的删除

    path('feedback/', FeedbackView.as_view({'post': 'create'}))  # profile页面用户反馈，现在已取消
]
