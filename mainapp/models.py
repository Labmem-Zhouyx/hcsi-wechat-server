from django.db import models

# Create your models here.
class UserEntity(models.Model):
    openid = models.CharField(max_length=20, default='')
    username = models.CharField(max_length=20, default='')
    email = models.CharField(max_length=50, default='')
    github_username = models.CharField(max_length=30, default='')
    status = models.CharField(max_length=20, default='disabled')
    class Meta:
        db_table = 't1_user'

class CaptchaList(models.Model):
    captcha = models.CharField(max_length=30)
    openid = models.CharField(max_length=20, default='')
    email = models.CharField(max_length=50, default='')

class EmailList(models.Model):
    email = models.CharField(max_length=50, default='')