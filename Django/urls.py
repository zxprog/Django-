# _*_ encoding:utf-8 _*_
"""Django URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.11/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import url, include
from django.contrib import admin
from django.views.static import serve

from Django.settings import MEDIA_ROOT#, STATIC_ROOT
from message.views import getform,getform2
from message import views
import  xadmin
from django.views.generic import TemplateView
#from django.urls import path
from users.views import LoginView, RegisterView, AciveUserView, ForgetPwdView, ResetView, ModifyPwdView, LogoutView, \
    IndexView

urlpatterns = [
    url(r'^xadmin/', xadmin.site.urls),
    url(r'^form/$', getform),
    url(r'^form2/', getform2),
    url(r'^test/', views.test_response),
    url(r'^test_html/', views.test_response_html),
    url('^$',IndexView.as_view(),name="index"),
    url('^login/$',LoginView.as_view(),name="login"),
    url('^logout/$',LogoutView.as_view(),name="logout"),
    url('^register/$',RegisterView.as_view(),name="register"),

    url(r'^captcha/', include('captcha.urls')),
    url(r'^active/(?P<active_code>.*)/$', AciveUserView.as_view(), name="user_active"),
    url(r'^forget/$', ForgetPwdView.as_view(), name="forget_pwd"),
    url(r'^reset/(?P<active_code>.*)/$', ResetView.as_view(), name="pwd_reset"),
    url(r'^modify/$', ModifyPwdView.as_view(), name="modify_pwd"),

    #课程机构url配置
    url(r'^org/', include('organization.urls', namespace="org")),

    #课程相关url配置
    url(r'^course/', include('courses.urls', namespace="course")),
    url(r'^media/(?P<path>.*)$',  serve, {"document_root":MEDIA_ROOT}),
    #课程相关url配置
    #url(r'^static/(?P<path>.*)$',  serve, {"document_root":STATIC_ROOT}),
    url(r'^users/', include('users.urls', namespace="users")),


]
handler404 = 'users.views.page_not_found'
handler500 = 'users.views.page_error'
