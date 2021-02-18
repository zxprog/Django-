# _*_ encoding:utf-8 _*_
from captcha.fields import CaptchaField
from django import forms

from users.models import UserProfile


class LoginForm(forms.Form):
    username = forms.CharField(required=True) #form里的变量名必须和前端里标签的Name相同，不然没办法定位
    password = forms.CharField(required=True,min_length=5)

class RegisterForm(forms.Form):
    email = forms.EmailField(required=True)
    password = forms.CharField(required=True, min_length=5)
    captcha = CaptchaField(error_messages={"invalid":u"验证码错误"})#不同的field会生成不同的Html代码

class ForgetForm(forms.Form):
    email = forms.EmailField(required=True)
    captcha = CaptchaField(error_messages={"invalid":u"验证码错误"})#不同的field会生成不同的Html代码

class ModifyPwdForm(forms.Form):
    password1 = forms.CharField(required=True,min_length=5) #form里的变量名必须和前端里标签的Name相同，不然没办法定位
    password2 = forms.CharField(required=True,min_length=5)


class UploadImageForm(forms.ModelForm):

    class Meta:
        model = UserProfile
        fields = ['image']

class UserInfoForm(forms.ModelForm):

    class Meta:
        model = UserProfile
        fields = ['nick_name','birday','gender','address','mobile']
