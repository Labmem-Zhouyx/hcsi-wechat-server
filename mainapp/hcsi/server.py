import os
import sys
sys.path.append(os.path.dirname(__file__))
import uuid
import logging
from mainapp.hcsi.cmd import run_cmd
from tornado.log import enable_pretty_logging
from tornado.options import options

options.logging = 'debug'
logger = logging.getLogger()
enable_pretty_logging(options=options, logger=logger)


servers = []
for i in [2, 3, 4, 5]:
    servers.append('hcsi-server%d' % i)
for i in [10, 11, 12]:
    servers.append('mjrc-server%d' % i)


def check_user(username, server):
    command = ['ssh', server, "grep -c '^%s:' /etc/passwd" % username]
    try:
        output = run_cmd(command)
    except Exception as e:
        output = e.output
    output = output.strip('\n')
    if output == '0':
        return False
    elif output == '1':
        return True
    else:
        raise RuntimeError


def create_user(username, server, uid):
    command = ['ssh', server, f"sudo useradd -m -g users -s /bin/bash -u {uid} {username}"]
    run_cmd(command)


def reset_password(username, server, password):
    command = ['ssh', server, "echo '%s:%s' | sudo chpasswd" % (username, password)]
    run_cmd(command, silent=True)


def get_ip(server):
    command = ['ssh', server, 'ip addr show']
    return run_cmd(command, silent=True)


def useradd(username, uid):
    user_message = ['Dear {0}:\n\n您好，\n\n您的服务器账户信息已创建/重置成功，请根据以下信息登录使用服务器:'.format(username)]
    for server in servers:
        if check_user(username, server):
            logger.info('User %s found on server %s.' % (username, server))
        else:
            logger.info('Creating user %s on server %s ...' % (username, server))
            create_user(username, server, uid)
        passwd = str(uuid.uuid1()).replace('-', '')
        logger.info('Setting password for user %s on server %s ...' % (username, server))
        reset_password(username, server, passwd)
        ip = get_ip(server)

        user_message.append('Server {0} 密码为{1} ，ip为{2}'.format(server, passwd, ip))
    user_message.append('Best wishes,\n\nTHU-HCSI')
    email_text = '\n\n'.join(user_message)   # 邮件正文
    email_subject = '用户{0}服务器账户信息创建/重置成功'.format(username)   # 邮件标题

    mini_program_subject = '用户{0}服务器账户信息创建/重置成功！用户信息已发送到您的电子邮箱，请注意查收。'.format(username)  # 小程序通知正文
    mini_program_text = '服务器账户创建/重置成功！'   # 小程序通知标题

    result_dict = {'email': {'subject': email_subject,
                             'text': email_text},
                   'mini_program': {'subject': mini_program_subject,
                                    'text': mini_program_text}}
    return result_dict
