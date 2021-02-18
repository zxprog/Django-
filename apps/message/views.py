# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.http import HttpResponse
from django.shortcuts import render

# Create your views here.
from message.models import UserMessage


def getform(request):#类似java中的socket流
    # messages = UserMessage.objects.all()
    # for m in messages:
    #     print(m.name)
    if request.method == "POST":
        name = request.POST.get("name")
        address = request.POST.get("address")
        email = request.POST.get("email")
        message = request.POST.get("message")
    # print(UserMessage.objects.filter(name="bobby")[0].address)
        new_person = UserMessage()
        new_person.name = name
        new_person.address = address
        new_person.object_id = "helloworld3"
        new_person.message = message
        new_person.email = email
        new_person.save()
    return render(request,"message_form.html")

def getform2(request):#类似java中的socket流


    p = UserMessage.objects.filter(name="bobby")[0]
    print(p.name)
    return render(request,"message_form.html",{"my_message":p})

def test_response(request):
    return HttpResponse("HelloWorld")


def test_response_html(request):
    return HttpResponse("<h1>这里是html返回练习</h1>")