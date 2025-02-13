from django.shortcuts import render
from django.contrib.auth import login as auth_login, authenticate, logout as auth_logout
from .forms import CustomUserCreationForm, CustomErrorList
from django.shortcuts import redirect
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail, get_connection, BadHeaderError
from django.conf import settings
from django.urls import reverse_lazy
from django.contrib.auth.views import PasswordResetView
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator
from django.contrib.sites.shortcuts import get_current_site
from smtplib import SMTPException
import socket
import smtplib

@login_required
def orders(request):
    template_data = {}
    template_data['title'] = 'Orders'
    template_data['orders'] = request.user.order_set.all()
    return render(request, 'accounts/orders.html',
        {'template_data': template_data})
def logout(request):
    auth_logout(request)
    return redirect('home.index')
def login(request):
    template_data = {}
    template_data['title'] = 'Login'
    if request.method == 'GET':
        return render(request, 'accounts/login.html', {'template_data': template_data})
    elif request.method == 'POST':
        user = authenticate(
            request,
            username = request.POST['username'],
            password = request.POST['password']
        )
        if user is None:
            template_data['error'] = 'The username or password is incorrect.'
            return render(request, 'accounts/login.html',
                {'template_data': template_data})
        else:
            auth_login(request, user)
            return redirect('home.index')

def signup(request):
    template_data = {}
    template_data['title'] = 'Sign Up'
    if request.method == 'GET':
        template_data['form'] = CustomUserCreationForm()
        return render(request, 'accounts/signup.html',
            {'template_data': template_data})
    elif request.method == 'POST':
        form = CustomUserCreationForm(request.POST, error_class=CustomErrorList)
        if form.is_valid():
            # Save the user but don't commit to database yet
            user = form.save(commit=False)
            # Set email
            user.email = form.cleaned_data['email']
            # Now save to database
            user.save()
            return redirect('accounts.login')
        else:
            template_data['form'] = form
            return render(request, 'accounts/signup.html',
                {'template_data': template_data})
        
class ResetPasswordView(PasswordResetView):
    template_name = 'accounts/password_reset.html'
    email_template_name = 'accounts/password_reset_email.html'
    subject_template_name = 'accounts/password_reset_subject.txt'
    success_url = reverse_lazy('accounts.login')
    
    def form_valid(self, form):
        print("\n=== Password Reset Debug ===")
        print("1. Form submitted")
        email = form.cleaned_data['email']
        print(f"2. Email address: {email}")
        
        try:
            users = list(form.get_users(email))
            print(f"3. Found users: {len(users)}")
            user = users[0] if users else None
            
            if user:
                print("4. User found, generating token...")
                token = default_token_generator.make_token(user)
                uid = urlsafe_base64_encode(force_bytes(user.pk))
                current_site = get_current_site(self.request)
                reset_url = f"{self.request.scheme}://{current_site.domain}/accounts/password-reset-confirm/{uid}/{token}/"
                print(f"5. Reset URL: {reset_url}")
                
                message = f"""
                Hello,
                
                You requested a password reset for your Movies Store account.
                Click the link below to reset your password:
                
                {reset_url}
                
                If you didn't request this, you can ignore this email.
                
                Thanks,
                Movies Store Team
                """
                print("6. Email message prepared")
                
                try:
                    print("\n=== Email Sending Attempt ===")
                    print(f"From: {settings.EMAIL_HOST_USER}")
                    print(f"To: {email}")
                    print("Message preview:")
                    print(message[:200] + "...")
                    
                    send_mail(
                        "Movies Store Password Reset",
                        message,
                        settings.EMAIL_HOST_USER,
                        [email],
                        fail_silently=False,
                    )
                    print("7. Email sent successfully")
                except BadHeaderError as e:
                    print(f"ERROR - Invalid header: {str(e)}")
                    raise
                except smtplib.SMTPException as e:
                    print(f"ERROR - SMTP error: {str(e)}")
                    raise
                except Exception as e:
                    print(f"ERROR - Unexpected: {type(e).__name__}: {str(e)}")
                    raise
                
                print("8. Process completed successfully")
            else:
                print("ERROR - No user found with this email")
            
            return super().form_valid(form)
            
        except Exception as e:
            print(f"ERROR in form_valid: {type(e).__name__}: {str(e)}")
            raise