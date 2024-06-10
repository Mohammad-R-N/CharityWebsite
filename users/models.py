from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator
from .helper import make_image_path
from django.utils.translation import gettext_lazy as _
from .enums import *

# Create your models here.


_REGEX = r"09(\d{9})$"
phone_validator = RegexValidator(_REGEX)

# class Job(models.Model):
#     en_name = models.CharField(_("english name"), max_length=60)
#     fa_name = models.CharField(_("persian name"), max_length=60, null=True, blank=True)
#     description = models.CharField(_("description"), max_length=300, null=True, blank=True)
#     date_added = models.DateTimeField(_("date added"), auto_now=True)
#     date_modified = models.DateTimeField(_("date modified"), auto_now_add=True)

#     def __str__(self) -> str:
#         return self.fa_name or self.en_name


class Volunteer(models.Model):
    first_name = models.CharField(verbose_name=_("first name"), max_length=100)
    last_name = models.CharField(verbose_name=_("last name"), max_length=100)
    email = models.EmailField(verbose_name=_("email"), unique=True)
    birth = models.DateField(verbose_name=_("birth day"))
    nc = models.BigIntegerField(verbose_name=_("nc"))
    major = models.CharField(verbose_name=_("major"), max_length=100)
    city = models.CharField(verbose_name=_("city"), max_length=100)
    phone = models.CharField(
        verbose_name=_("phone"),
        max_length=14,
        validators=[phone_validator],
        unique=True,
    )
    specialist_info = models.TextField(verbose_name=_("specialist info"))
    profile_pic = models.ImageField(
        verbose_name=_("profile picture"),
        upload_to=make_image_path(first_name, last_name),
    )
    abilities = models.CharField(
        max_length=100, choices=ABILITIES_CHOICES, default="piping"
    )
    marital_status = models.PositiveSmallIntegerField(
        verbose_name=_("marital status"), choices=MARITAL_CHOICES
    )
    gender = models.PositiveSmallIntegerField(
        verbose_name=_("gender"), choices=GENDER_CHOICES
    )
    education = models.PositiveSmallIntegerField(
        verbose_name=_("education"), choices=EDU_CHOICES
    )
    experience_info = models.TextField(verbose_name=_("experience info"))


class User(AbstractUser):
    first_name = models.CharField(
        verbose_name=_("first name"), max_length=100, null=True, blank=True
    )
    last_name = models.CharField(
        verbose_name=_("last name"), max_length=100, null=True, blank=True
    )
    email = models.EmailField(
        verbose_name=_("email"), unique=True, null=True, blank=True
    )
    city = models.CharField(
        verbose_name=_("city"), max_length=100, null=True, blank=True
    )
    phone = models.CharField(
        verbose_name=_("phone"),
        max_length=14,
        validators=[phone_validator],
        unique=True,
    )
    volunteer_info = models.OneToOneField(
        Volunteer, on_delete=models.SET_NULL, null=True, blank=True
    )
