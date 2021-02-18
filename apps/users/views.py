# _*_ encoding:utf-8 _*_
import json
from smtplib import SMTPRecipientsRefused
from socket import timeout

from django.core.cache import cache
from django.core.urlresolvers import reverse
from django.contrib.auth.hashers import make_password
from django.core.paginator import PageNotAnInteger
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.contrib.auth import authenticate, login, logout

from django.contrib.auth.backends import ModelBackend
from  django.db.models import Q
from django.views.decorators.cache import cache_page
from django.views.generic.base import View
from pure_pagination import Paginator

from courses.models import Course
from operation.models import UserCourse, UserFavorite, UserMessage
from organization.models import CourseOrg, Teacher
from utils.email_send import send_register_email
from utils.mixin_utils import LoginRequiredMixin
from .models import UserProfile, EmailVerifyRecord, Banner
from form import LoginForm, RegisterForm, ForgetForm, ModifyPwdForm, UploadImageForm, UserInfoForm


# Create your views here.
#重写后台的授权方法，使得可以通过邮箱登陆
class CustomBackend(ModelBackend):
    def authenticate(self, username=None, password=None, **kwargs):
        try:
            user = UserProfile.objects.get(Q(username=username)|Q(email=username))
            if user.check_password(password):
                return user
            return None
        except Exception as e :
            return None
class LogoutView(View):
    def get(self,request):
        logout(request)
        from django.core.urlresolvers import reverse
        return HttpResponseRedirect(reverse("index"))#这里不返回网页，而是重定向
class LoginView(View):
    def get(self,request):
        return render(request,"login.html")
    def post(self,request):
        login_form = LoginForm(request.POST)
        if login_form.is_valid():
            user_name = request.POST.get("username","")
            pass_word = request.POST.get("password","")
            user = authenticate(username = user_name,password=pass_word)
            if user:
                #登陆
                if user.is_active:
                    login(request,user) #登陆
                    return HttpResponseRedirect(reverse("index"))
                else:
                    return render(request, "login.html", {"msg": "用户未激活！"})
            else:
                return render(request,"login.html",{"msg":"用户名或密码错误"})
        else:
            return render(request,"login.html",{"login_form":login_form})


class AciveUserView(View):
    def get(self, request, active_code):
        #all_records = EmailVerifyRecord.objects.filter(code=active_code2)
        record = EmailVerifyRecord.objects.get(code=active_code)
        if record:
        #if all_records:
            #for record in all_records:
            email = record.email
            user = UserProfile.objects.get(email=email) #将用这个邮箱注册的用户取出来激活
            user.is_active = True  #激活完，应该将那条记录删掉
            user.save()
            record.delete()
        else:
            return render(request, "active_fail.html")
        return render(request, "login.html")

class RegisterView(View):
    def get(self, request):
        register_form = RegisterForm()#返回一张带有验证码的页面
        return render(request, "register.html", {'register_form':register_form})#给页面上传参

    def post(self, request):
        register_form = RegisterForm(request.POST)#表单验证
        if register_form.is_valid():
            user_name = request.POST.get("email", "")
            if UserProfile.objects.filter(email=user_name):
                return render(request, "register.html", {"register_form":register_form, "msg":"用户已经存在"})
            pass_word = request.POST.get("password", "")
            user_profile = UserProfile()
            user_profile.username = user_name
            user_profile.email = user_name
            user_profile.is_active = False
            user_profile.password = make_password(pass_word)#加密
            user_profile.save()

            # #写入欢迎注册消息
            user_message = UserMessage()
            user_message.user = user_profile.id
            user_message.message = "欢迎注册慕学在线网"
            user_message.save()
            #
            try:
                send_register_email(user_name, "register")
                return render(request, "login.html")
            except SMTPRecipientsRefused as e:
                print("邮箱不存在")
                return render(request, "register.html", {"register_form":register_form, "msg":"邮箱不存在"})

        else:
            return render(request, "register.html", {"register_form":register_form})
class ForgetPwdView(View):
    def get(self,request):
        forget_form = ForgetForm()
        return render(request, "forgetpwd.html",{"forget_form":forget_form})
    def post(self,request):
        forget_form = ForgetForm(request.POST)
        if forget_form.is_valid():
            email = request.POST.get("email")
            user = UserProfile.objects.get(email=email)
            if user:
                send_register_email(email,send_type="forget")
                return HttpResponse("<h1>邮件已经成功发出，请查收！</h1>")
            else:
                return HttpResponse("<h1>该邮箱未被注册过！</h1>")
        else:
            return render(request, "forgetpwd.html",{"forget_form":forget_form})    #填写的邮箱格式就不对

class ResetView(View):
    def get(self, request, active_code):
        all_records = EmailVerifyRecord.objects.filter(code=active_code)
        if all_records:
            for record in all_records:
                email = record.email
                return render(request, "password_reset.html", {"email":email})#把用户email传入后台
        else:
            return render(request, "active_fail.html")
        return render(request, "login.html")

class ModifyPwdView(View):
    """
    修改用户密码
    """
    def post(self, request):
        modify_form = ModifyPwdForm(request.POST)
        if modify_form.is_valid():
            pwd1 = request.POST.get("password1", "")
            pwd2 = request.POST.get("password2", "")
            email = request.POST.get("email", "")
            if pwd1 != pwd2:
                return render(request, "password_reset.html", {"email":email, "msg":"密码不一致"})
            user = UserProfile.objects.get(email=email)
            user.password = make_password(pwd2)
            user.save()
            return render(request, "login.html")
        else:
            email = request.POST.get("email", "")
            return render(request, "password_reset.html", {"email":email, "modify_form":modify_form})


class SendEmailCodeView(LoginRequiredMixin, View):
    """
    发送邮箱验证码
    """
    def get(self, request):
        email = request.GET.get('email', '')

        if UserProfile.objects.filter(email=email):
            return HttpResponse('{"email":"邮箱已经存在"}', content_type='application/json')
        send_register_email(email, "update_email")#更新邮箱

        return HttpResponse('{"status":"success"}', content_type='application/json')


class UpdateEmailView(LoginRequiredMixin, View):
    """
    修改个人邮箱
    """
    def post(self, request):
        email = request.POST.get('email', '')
        code = request.POST.get('code', '')

        existed_records = EmailVerifyRecord.objects.filter(email=email, code=code, send_type='update_email')
        if existed_records:
            user = request.user
            user.email = email
            user.save()
            return HttpResponse('{"status":"success"}', content_type='application/json')
        else:
            return HttpResponse('{"email":"验证码出错"}', content_type='application/json')


class MyCourseView(LoginRequiredMixin, View):
    """
    我的课程
    """
    def get(self, request):
        current_page = 'mycourse'
        user_courses = UserCourse.objects.filter(user=request.user)
        return render(request, 'usercenter-mycourse.html', {
            "user_courses":user_courses,
            "current_page":current_page
        })


class MyFavOrgView(LoginRequiredMixin, View):
    """
    我收藏的课程机构
    """
    def get(self, request):
        org_list = []
        fav_orgs = UserFavorite.objects.filter(user=request.user, fav_type=2)
        print(len(fav_orgs))
        currentpage = 'org'
        #因为fav_id没有外键，所以必须都取出来
        # for fav_org in fav_orgs:
        #     org_id = fav_org.fav_id
        #     org = CourseOrg.objects.get(id=org_id)
        #     org_list.append(org)
        org_list = list(map(lambda x:CourseOrg.objects.get(id=x.fav_id),fav_orgs))
        return render(request, 'usercenter-fav-org.html', {
            "org_list":org_list,
            "current_page": "mayfav",
            "currentpage": currentpage
        })


class MyFavTeacherView(LoginRequiredMixin, View):
    """
    我收藏的授课讲师
    """
    def get(self, request):
        currentpage = 'teacher'
        # teacher_list = []
        fav_teachers = UserFavorite.objects.filter(user=request.user, fav_type=3)
        # for fav_teacher in fav_teachers:
        #     teacher_id = fav_teacher.fav_id
        #     teacher = Teacher.objects.get(id=teacher_id)
        #     teacher_list.append(teacher)
        teacher_list  = list(map(lambda x: Teacher.objects.get(id=x.fav_id), fav_teachers))
        return render(request, 'usercenter-fav-teacher.html', {
            "teacher_list":teacher_list,
            "current_page": "mayfav",
            "currentpage":currentpage
        })


class MyFavCourseView(LoginRequiredMixin, View):
    """
    我收藏的课程
    """
    def get(self, request):
        currentpage = 'course'
        #course_list = []
        fav_courses = UserFavorite.objects.filter(user=request.user, fav_type=1)
        # for fav_course in fav_courses:
        #     course_id = fav_course.fav_id
        #     teacher = Course.objects.get(id=course_id)
        #     course_list.append(teacher)
        course_list = list(map(lambda x: Course.objects.get(id=x.fav_id), fav_courses))
        return render(request, 'usercenter-fav-course.html', {
            "course_list":course_list,
            "current_page":"mayfav",
            "currentpage": currentpage
        })

class ModifyPwdView(View):
    """
    修改用户密码
    """
    def post(self, request):
        modify_form = ModifyPwdForm(request.POST)
        if modify_form.is_valid():
            pwd1 = request.POST.get("password1", "")
            pwd2 = request.POST.get("password2", "")
            email = request.POST.get("email", "")
            if pwd1 != pwd2:
                return render(request, "password_reset.html", {"email":email, "msg":"密码不一致"})
            user = UserProfile.objects.get(email=email)
            user.password = make_password(pwd2)
            user.save()

            return render(request, "login.html")
        else:
            email = request.POST.get("email", "")
            return render(request, "password_reset.html", {"email":email, "modify_form":modify_form})


class UserinfoView(LoginRequiredMixin, View):
    """
    用户个人信息
    """
    def get(self, request):
        current_page = "user_info"
        return render(request, 'usercenter-info.html', {"current_page":current_page})

    def post(self, request):
        user_info_form = UserInfoForm(request.POST, instance=request.user)
        if user_info_form.is_valid():
            user_info_form.save()
            return HttpResponse('{"status":"success"}', content_type='application/json')
        else:
            return HttpResponse(json.dumps(user_info_form.errors), content_type='application/json')




class UploadImageView(LoginRequiredMixin, View):
    """
    用户修改头像
    """
    def post(self, request):
        image_form = UploadImageForm(request.POST, request.FILES, instance=request.user)
        if image_form.is_valid():
            image_form.save()
            return HttpResponse('{"status":"success"}', content_type='application/json')
        else:
            return HttpResponse('{"status":"fail"}', content_type='application/json')



class UpdatePwdView(View):
    """
    个人中心修改用户密码
    """
    def post(self, request):
        modify_form = ModifyPwdForm(request.POST)
        if modify_form.is_valid():
            pwd1 = request.POST.get("password1", "")
            pwd2 = request.POST.get("password2", "")
            if pwd1 != pwd2:
                return HttpResponse('{"status":"fail","msg":"密码不一致"}', content_type='application/json')
            user = request.user
            user.password = make_password(pwd2)
            user.save()

            return HttpResponse('{"status":"success"}', content_type='application/json')
        else:
            return HttpResponse(json.dumps(modify_form.errors), content_type='application/json')


class MymessageView(LoginRequiredMixin,View):
    def get(self,request):
        current_page = 'message'
        user_message = UserMessage.objects.filter(user=request.user.id)
        # 用户进入个人消息后清空未读消息的记录
        all_unread_messages = UserMessage.objects.filter(user=request.user.id, has_read=False)
        for unread_message in all_unread_messages:
            unread_message.has_read = True
            unread_message.save()
        try:
            page = request.GET.get('page', 1)
        except PageNotAnInteger:
            page = 1

        p = Paginator(user_message, 5, request=request)

        messages = p.page(page)
        return render(request,'usercenter-message.html',{"current_page":current_page,"messages":messages})

class IndexView(View):
    #慕学在线网 首页
    def get(self, request):
        #取出轮播图

        all_banners = Banner.objects.all().order_by('index')
        courses = Course.objects.filter(is_banner=False)[:6]
        banner_courses = Course.objects.filter(is_banner=True)[:3]
        course_orgs = CourseOrg.objects.all()[:15]
        context =  {
            'all_banners':all_banners,
            'courses':courses,
            'banner_courses':banner_courses,
            'course_orgs':course_orgs
        }
        response = render(request, 'index.html', context)

        return response


def page_not_found(request):
    #全局404处理函数
    from django.shortcuts import render_to_response
    response = render_to_response('404.html', {})
    response.status_code = 404
    return response

def page_error(request):
    #全局500处理函数
    from django.shortcuts import render_to_response
    response = render_to_response('500.html', {})
    response.status_code = 500
    return response

class Session1(View):
    def get(self,request):
        # result = cache.get('news')
        # if result:
        #     return HttpResponse(result)
        uname = request.GET.get("uname","")
        request.session['myname'] = uname
        request.session.set_expiry(10)
        response = render(request, 'session1.html')
        # cache.set("news", response.content)
        return response

class Session2(View):
    def get(self,request):
        uname = request.session.get('myname','未登录')
        return render(request,'session2.html',{"uname":uname})
