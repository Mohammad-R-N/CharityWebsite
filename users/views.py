from django.core.validators import RegexValidator
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.http import JsonResponse
from django.contrib import messages, auth
from django.views import View
from django.conf import settings
from django.utils.translation import gettext_lazy as _

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status


import json, re
from datetime import datetime, timedelta
from Charity.settings import mail

from .forms import ContactUsForm, VolunteerRegisterForm, RegisterForm
from .authentication import OtpAuthBackend, UserAuthBackend
from .models import User
from .utils import generate_otp_code, send_otp_code
# Create your views here.

def home(request) :
    if request.method == "POST":
        form = ContactUsForm(request.POST or None)
        if form.is_valid():
            cd = form.cleaned_data
            name = cd['name']
            email = cd['email']
            subject = cd['subject']
            content = cd['content']
            message = "نام:{0}\n ایمیل:{1}\n پیام:{3}".format(name, email, content)
            send_mail(subject, message, mail, [settings.Contact_Us_Email] ,fail_silently=False)
    else :
        form = ContactUsForm()
        context = {'form' : form}
    return render(request, "home.html", context)


def volunteer_register(request):
    if request.method == "POST":
        form = VolunteerRegisterForm(request.POST or None, request.FILES)
        if form.is_valid():
            user = request.user
            if not isinstance(user, User):
                clean_data = form.cleaned_data.copy()
                clean_data.update({'username': f"{clean_data['first_name']}"})
                user = RegisterForm(form.data)
                user = user.save()

            volunteer_form = form.save(commit=False)
            volunteer_form.user = user
            volunteer_form.save()
            messages.success(request, 'به جمع داوطلبین خادمین سیده زینب خوش آمدید')
            return redirect('users:volunteer')
    prefill_data = request.GET.copy()
    if isinstance(request.user, User):
        prefill_data.update({'first_name':request.user.first_name, 'last_name': request.user.last_name, 'phone':request.user.phone})
    form = VolunteerRegisterForm(initial=prefill_data)
    return render(request, "users/volunteer.html", {"form": form})

def about_us(request) :
    return render (request, 'about.html')

_REGEX = re.compile(r'09(\d{9})$')

class PhoneValidationView(View) :
    def post(self, request) :
        data = json.loads(request.body)
        phone = data['phone']

        if not re.fullmatch(_REGEX, phone) :
            return JsonResponse({'PhoneValidationError' : 'شماره وارد شده صحیح نمیباشد'}, status=400)
        
        if User.objects.filter(phone=phone).exists :
            return JsonResponse({'PhoneError' : 'این شماره تماس قبلا استفاده شده'}, status=409)
        return JsonResponse({'username_valid' : True})
    

class RegistrationView(View) :
    def get(self, request) :
        return render(request, 'users/register.html')
    
    def post(self, request) :
        phone = request.POST['phone']
        password1 = request.POST['password1']
        password2 = request.POST['password2']

        context ={
            'fieldValues' : request.POST
        }
        if User.objects.filter(phone=phone).exists() :
            messages.error(request, 'این شماره تماس قبلا استفاده شده')
            return render(request, 'users/register.html')
        
        elif password1 != password2 :
            messages.error(request, 'رمز عبور مطابقت ندارد')
            return render(request, 'users/register.html', context)
        
        elif len(password1) < 4:
            messages.error(request, 'رمز عبور کوتاه است')
            return render(request, 'users/register.html', context)
        
        else :
            user = User.objects.create(phone=phone)
            if password1 is not None:
                user.set_password(password1)
            else:
                messages.error(request, "رمز عبور نمیتواند خالی باشد")
                return render(request, 'users/register.html', context)
            user.save()
            messages.success(request, 'حساب کاربری با موفقیت ساخته شد')
            return user


class LoginView(View) :
    def get(self, request) :
        return render(request, 'users.login.html')
    
    def post(self,request) :
        phone = request.POST['phone']
        password1 = request.POST['pasword1']

        if phone and password1 :
            user = auth.authenticate(phone=phone, password=password1)
            if user :
                auth.login(request, user)
                messages.success(request, 'خوش اومدی')
        
            messages.error(request, 'شماره موبایل یا رمز عبور اشتباه است')
            return render(request, 'users/login.html')
        messages.error(request, 'لطفا شماره موبایل و رمز عبور را وارد کنید')
        return render(request, 'users/login.html')
    

class LogoutView(View) :
    def post(self, request) :
        auth.logout(request)
        messages.success(request, 'از حساب کاربری خارج شدید')
        return redirect('login')
    

@login_required(login_url='users/login')
def dashboard(request) :
    return render(request, 'users/dashboard.html')


class OtpView(APIView):
    def get(self, request):
        if request.user and isinstance(request.user, User):
            return Response(
                data={"data":None, "message":_("user is already logged in")},
                status=status.HTTP_400_BAD_REQUEST
            )
        otp_type = request.GET.get("otp_type")
        otp_identifier = request.GET.get("otp_identifier")
        if otp_type in ["sms", "email"]:
            if otp_identifier:
                otp_code = generate_otp_code()
                request.session['otp_code'] = otp_code
                request.session['otp_identifier'] = otp_identifier
                request.session['otp_expire_time'] = datetime.now() + settings.OTP_EXPIRE_TIME
                send_otp_code(otp_code, otp_type, otp_identifier)
                message = _("code has sent to {otp_identifier}").format(otp_identifier=otp_identifier)
                return Response(
                    data={"data":None, "message":message},
                    status=status.HTTP_200_OK
                )
            return Response(
                data={"data":None, "message":_("otp identifier has bot provided")},
                status=status.HTTP_400_BAD_REQUEST
            )
        return Response(
            data={"data":None, "message":_("invalid otp type")},
            status=status.HTTP_400_BAD_REQUEST
        )
        

    def post(self, request):
        otp_request = request.query_params.get("otp_request")
        if otp_request == "login":
            return self.verify_login_otp(request)
        if otp_request == "verify_otp":
            return self.verify_otp(request)
    
    def verify_login_otp(self, request):
        otp_code = request.POST.get("otp_code")
        user = OtpAuthBackend().authenticate(request, otp_code=otp_code)
        if user:
            auth.login(request, user, backend='accounts.authentication.OtpAuthBackend')
            del request.session["otp_code"]
            del request.session["otp_expire_time"]
            del request.session["otp_identifier"]
            message =  _('You have been logged in successfully')
            messages.success(request, message)
            return Response(
                    data={"data":None, "message":message},
                    status=status.HTTP_200_OK
            )
        messages.error(request, _('invalid otp'))
        return Response(
            data={"data":None, "message":_("invalid otp type")},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    def verify_otp(self, request):
        otp_code = request.POST.get("otp_code")
        if OtpAuthBackend().verify_otp(request, otp_code=otp_code):
            return Response(
                    data={"data":None, "message":_("otp veified successfully")},
                    status=status.HTTP_200_OK
            )
        messages.error(request, _('invalid otp'))
        return Response(
            data={"data":None, "message":_("invalid otp")},
            status=status.HTTP_400_BAD_REQUEST
        )