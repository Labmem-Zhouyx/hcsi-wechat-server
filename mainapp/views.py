from django.shortcuts import render, HttpResponse, redirect, get_object_or_404
from django.http import JsonResponse
from mainapp.models import UserEntity, CaptchaList, EmailList
from django.core.mail import send_mail
from HCSIserver.settings import EMAIL_FROM
from django.views.decorators.csrf import csrf_exempt
from mainapp.hcsi import server, github_
import random
import time
import hashlib
import json
import re


# Create your views here.
def user_list(request):
    users = UserEntity.objects.all()
    return render(request, 'user/list.html', locals())


def user_add(request):
    if request.method == 'GET':
        u1 = UserEntity()
        u1.username = request.GET.get('username', '')
        u1.openid = request.GET.get('openid', '')
        u1.email = request.GET.get('email', '')
        u1.github_username = request.GET.get('github_username', '')
        u1.save()
    if request.method == 'POST':
        u1 = UserEntity()
        u1.username = request.POST.get('username', '')
        u1.openid = request.POST.get('openid', '')
        u1.email = request.POST.get('email', '')
        u1.github_username = request.POST.get('github_username', '')
        u1.save()
    mini_program_subject = 'Add user successfully.'
    mini_program_text = f'用户加入成功。'
    ret = {'email': {},
                   'mini_program': {'mini_program_subject': mini_program_subject,
                                    'mini_program_text': mini_program_text}}
    return JsonResponse(ret)


def user_edit(request):
    if request.method == 'GET':
        u1 = UserEntity.objects.get(email=request.GET.get('email'))
        u1.username = request.GET.get('username', u1.username)
        u1.openid = request.GET.get('openid', u1.openid)
        u1.github_username = request.GET.get('github_username',  u1.github_username)
        u1.save()
    if request.method == 'POST':
        u1 = UserEntity.objects.get(email=request.POST.get('email'))
        u1.username = request.POST.get('username', u1.username)
        u1.openid = request.POST.get('openid', u1.openid)
        u1.github_username = request.POST.get('github_username', u1.github_username)
        u1.save()

    mini_program_subject = 'Edit user successfully.'
    mini_program_text = f'用户编辑成功。'
    ret = {'email': {},
                   'mini_program': {'mini_program_subject': mini_program_subject,
                                    'mini_program_text': mini_program_text}}
    return JsonResponse(ret)


def user_delete(request):
    if request.method == 'GET':
        u = UserEntity.objects.filter(email=request.GET.get('email'))
        u.delete()
    if request.method == 'POST':
        u = UserEntity.objects.filter(email=request.POST.get('email'))
        u.delete()

    mini_program_subject = 'Delete user successfully.'
    mini_program_text = f'用户删除成功。'
    ret = {'email': {},
                   'mini_program': {'mini_program_subject': mini_program_subject,
                                    'mini_program_text': mini_program_text}}
    return JsonResponse(ret)


def random_str():
    str = ''
    chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890'
    for i in range(20):
        str += chars[random.randint(0, len(chars) - 1)]
    return str


def common_check(request):
    data = request.POST.copy()
    nonce = request.POST.get('nonce', '')
    timestamp = request.POST.get('timestamp', time.time())
    timestamp_server = time.time()
    if abs(timestamp - timestamp_server) > 600:
        return False
    signature = data.pop('signature', '')
    j = json.dumps(sorted(data.items()))

    return (hashlib.sha256((j + 'secret').encode('utf-8')).hexdigest()) == signature


@csrf_exempt
def server_useradd(request):
    is_valid = common_check(request)
    print(is_valid)
    if request.method == 'GET':
        openid = request.GET.get('openid', '')
    if request.method == 'POST':
        openid = request.POST.get('openid', '')
    u = UserEntity.objects.filter(openid=openid).first()
    if u == None:
        mini_program_subject = 'Openid not added.'
        mini_program_text = f'用户openid未添加。'
        ret = {'email': {},
               'mini_program': {'subject': mini_program_subject,
                                'text': mini_program_text}}
    else:
        if u.status == 'enabled':
            uid = 2000 + u.id
            ret = server.useradd(u.username, uid)
        else:
            mini_program_subject = 'Openid not activated.'
            mini_program_text = f'用户openid未激活。'
            ret = {'email': {},
                   'mini_program': {'subject': mini_program_subject,
                                    'text': mini_program_text}}
    return JsonResponse(ret)


@csrf_exempt
def common_verification(request):
    c = CaptchaList.objects.filter(captcha=request.GET.get('captcha')).first()
    if c != None:
        u_exist = UserEntity.objects.filter(email = c.email).first()
        if u_exist:
            username = u_exist.username
            u_exist.status = 'enabled'
            u_exist.save()
        else:
            u = UserEntity()
            u.email = c.email
            u.openid = c.openid
            u.username = (c.email)[0:(c.email).find('@', 1)]
            username = u.username
            u.status = "enabled"
            u.save()
        mini_program_subject = 'User Authentication Passed.'
        mini_program_text = f'用户 {username} 激活成功。'
    else:
        mini_program_subject = 'Authentication Failed.'
        mini_program_text = f'用户激活失败。'
    ret = {'email': {},
           'mini_program': {'mini_program_subject': mini_program_subject,
                            'mini_program_text': mini_program_text}}
    return JsonResponse(ret)


@csrf_exempt
def common_authentication(request):
    is_valid = common_check(request)
    print(is_valid)

    if request.method == 'POST':
        target_email = request.POST.get('email')
        openid = request.POST.get('openid')
    if request.method == 'GET':
        target_email = request.GET.get('email')
        openid = request.GET.get('openid')
    u1 = UserEntity.objects.filter(email=target_email).first()
    if u1 == None:
        print('Add User Email:', target_email)
        ex_email = re.compile(r'^.+@mails\.tsinghua\.edu\.cn')
        is_THU_email = ex_email.match(target_email)
        if is_THU_email or (EmailList.objects.filter(email=target_email).first()):
            captcha = random_str()
            email_title = '注册邮箱激活链接'
            # 需修改host
            #host = "https://mjrc.sz.tsinghua.edu.cn"
            host = "http://219.223.184.110:8000"
            email_body = "点击该链接激活邮箱：" + host + "/hcsi/common/verification/?captcha={0}".format(captcha)
            c1 = CaptchaList()
            c1.captcha = captcha
            c1.email = target_email
            c1.openid = openid
            c1.save()
            send_status = send_mail(email_title, email_body, EMAIL_FROM, [target_email])
            if send_status:
                mini_program_subject = 'Not Exist, Send email to user.'
                mini_program_text = '用户未注册，已发送验证邮件至邮箱。'
            else:
                mini_program_subject = 'fail in send.'
                mini_program_text = '发送邮件失败。'
        else:
            mini_program_subject = 'illegal email.'
            mini_program_text = '不合法邮箱。'
    else:
        mini_program_subject = 'User Exist.'
        mini_program_text = '用户已存在。'
    ret = {'email': {},
           'mini_program': {'mini_program_subject': mini_program_subject,
                            'mini_program_text': mini_program_text}}
    return JsonResponse(ret)


def github_invitation(request):
    is_valid = common_check(request)
    print(is_valid)

    class GithubConfig:
        access_token = 'access_token'
        organization_name = 'organization_name'

    if request.method == 'GET':
        openid = request.GET.get('openid', '')
        username = request.GET.get('github_username', '')
    if request.method == 'POST':
        openid = request.POST.get('openid', '')
        username = request.POST.get('github_username', '')
    u = UserEntity.objects.filter(openid=openid).first()

    if u == None:
        mini_program_subject = 'Openid not added.'
        mini_program_text = f'用户openid未添加。'
        ret = {'email': {},
               'mini_program': {'subject': mini_program_subject,
                                'text': mini_program_text}}
    else:
        if u.status == 'enabled':
            u.github_username = username
            u.save()
            ret = github_.invite_user(username, GithubConfig)
        else:
            mini_program_subject = 'Openid not activated.'
            mini_program_text = f'用户openid未激活。'
            ret = {'email': {},
                       'mini_program': {'subject': mini_program_subject,
                                        'text': mini_program_text}}
    return JsonResponse(ret)
