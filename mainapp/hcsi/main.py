#!/bin/python3
import os
import sys
sys.path.append(os.path.dirname(__file__))
import uuid
import logging
import traceback
import re
import imaplib
import smtplib
from email.parser import HeaderParser
from email.header import decode_header
from cmd import run_cmd
from mailutils import assemble_mail

logger = logging.getLogger()
email_re = re.compile(r'<(([^@]*)@[^>]*)>$')
email_re_2 = re.compile(r'(([^@]*)@[^>]*)$')

servers= []
for i in [2, 3, 4, 5]:
    servers.append('hcsi-server%d' % i)
for i in [10, 11, 12]:
    servers.append('mjrc-server%d' % i)

def parse_email_address(text):
    try:
        return email_re.search(username).group(1), email_re.search(username).group(2)
    except:
        return email_re_2.search(username).group(1), email_re_2.search(username).group(2)

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

def create_user(username, server):
    command = ['ssh', server, "sudo useradd -m -g users -s /bin/bash %s" % username]
    run_cmd(command)

def reset_password(username, server, password):
    command = ['ssh', server, "echo '%s:%s' | sudo chpasswd" % (username, password)]
    run_cmd(command, silent=True)

def get_ip(server):
    command = ['ssh', server, 'ip addr show']
    return run_cmd(command, silent=True)


if __name__ == '__main__':
    from tornado.log import enable_pretty_logging
    from tornado.options import options
    from config import IMAPConfig
    
    options.logging = 'debug'
    logger = logging.getLogger()
    enable_pretty_logging(options=options, logger=logger)

    imap = imaplib.IMAP4_SSL(IMAPConfig.imap_server, IMAPConfig.imap_port)
    smtp = smtplib.SMTP_SSL(IMAPConfig.smtp_server, IMAPConfig.smtp_port)

    imap.login(IMAPConfig.account, IMAPConfig.password)
    imap.select()
    #imap.select('&g0l6P3ux-')
    #imap.select('&XfJT0ZAB-') #已发送
    #imap.select('&XfJSIJZk-') #已删除
    #imap.select('&V4NXPpCuTvY-')

    parser = HeaderParser()

    try:
        #logger.info('Checking for emails ...')
        try:
            typ, data = imap.search(None, 'FROM', 'edu')
        except:
            logger.warning(traceback.print_exc())
        #logger.info('Found %d new email(s) ...' % len(data[0].split()))

        for num in data[0].split():
            typ, data = imap.fetch(num, '(BODY[HEADER])')
            data = parser.parsestr(data[0][1].decode('utf-8'))
            username = data['From']
            sender, username = parse_email_address(username)
            server = data['Subject']
            if not 'edu' in sender[len(username):]:
                result = imap.copy(num, '&XfJSIJZk-')
                if result[0] == 'OK':
                    imap.store(num, '+FLAGS', '\\Deleted')
                    imap.expunge()
            try:
                server = decode_header(server)[0][0].decode('utf-8')
            except:
                pass
            logger.info('Processing request (%s, %s) ...' % (username, server))
            try:
                if server in servers:
                    if check_user(username, server):
                        logger.info('User %s found on server %s.' % (username, server))
                        subject = '%s 上的用户 %s 密码重置成功！' % (server, username)
                    else:
                        logger.info('Creating user %s on server %s ...' % (username, server))
                        subject = '%s 上的用户 %s 创建成功！' % (server, username)
                        create_user(username, server)
                    passwd = str(uuid.uuid1()).replace('-', '')
                    logger.info('Setting password for user %s on server %s ...' % (username, server))
                    reset_password(username, server, passwd)
                    message = ['密码为 %s' % passwd, get_ip(server)]
                    message = '\n\n'.join(message)
                    logger.info('Sending email to %s ...' % sender)
                    smtp.login(IMAPConfig.account, IMAPConfig.password)
                    smtp.send_message(assemble_mail(subject, sender, IMAPConfig.account, text=message))
                    smtp.quit()
            except Exception as e:
                message = [str(data), traceback.print_exc()]
                message = '\n\n'.join(message)
                smtp.login(IMAPConfig.account, IMAPConfig.password)
                smtp.send_message(assemble_mail('mailbot 爆炸啦', 'user@example.com', IMAPConfig.account, text=message))
                smtp.quit()
            finally:
                result = imap.copy(num, '&XfJSIJZk-')
                if result[0] == 'OK':
                    imap.store(num, '+FLAGS', '\\Deleted')
                    imap.expunge()
    finally:
        imap.close()
        imap.logout()
