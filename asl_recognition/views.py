from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.signing import TimestampSigner, SignatureExpired, BadSignature
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import update_session_auth_hash
from django.template.loader import render_to_string
import json
import base64
import numpy as np
from PIL import Image
import io
from .asl_predictor import get_predictor
from .forms import RegisterForm, LoginForm, ProfileForm, CustomPasswordChangeForm
from .models import GameScore, UserProfile
from django.contrib.auth.models import User
from .auth_backends import AdminBackend


def index(request):
    """Render the main ASL recognition page"""
    return render(request, 'asl_recognition/index.html')


def social_login_success(request):
    """Handle successful social login and communicate with parent window"""
    from django.contrib.auth import login
    from django.contrib.sessions.models import Session
    
    # Clear any existing sessions to prevent conflicts
    if request.user.is_authenticated:
        Session.objects.filter(session_key__in=list(request.session.keys())).delete()
    
    # Ensure the user is properly logged in
    if hasattr(request, 'user') and request.user.is_authenticated:
        login(request, request.user, backend='django.contrib.auth.backends.ModelBackend')
        messages.success(request, f'Welcome back, {request.user.username}!')
        return redirect('home')
    else:
        return render(request, 'socialaccount/login_success.html')


@csrf_exempt
def predict(request):
    """API endpoint to predict ASL sign from image data"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Only POST requests allowed'}, status=405)
    
    try:
        data = json.loads(request.body)
        image_data = data.get('image')
        
        if not image_data:
            return JsonResponse({'error': 'No image data provided'}, status=400)
        
        # Decode base64 image
        # Remove data URL prefix if present
        if ',' in image_data:
            image_data = image_data.split(',')[1]
        
        image_bytes = base64.b64decode(image_data)
        image = Image.open(io.BytesIO(image_bytes))
        
        # Convert to RGB if necessary
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        # Convert to numpy array
        image_array = np.array(image)
        
        # Get predictor and process
        predictor = get_predictor()
        result = predictor.process_frame(image_array)
        
        return JsonResponse(result)
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


def webcam(request):
    """Render the webcam-based ASL recognition page"""
    from django.conf import settings
    context = {
        'DATASET_URL': getattr(settings, 'DATASET_URL', '/dataset/'),
        'GUIDE_URL': getattr(settings, 'GUIDE_URL', '/guide/')
    }
    return render(request, 'asl_recognition/webcam.html', context)


def _send_verification_email(request, user):
    signer = TimestampSigner()
    token = signer.sign(user.pk)
    verify_link = request.build_absolute_uri('/verify-email/{}/'.format(token))
    subject = 'Verify your ASL account'
    message = (
        f'Hi {user.username},\n\n'
        f'Please verify your email by clicking the link below:\n{verify_link}\n\n'
        'If you did not register, please ignore this email.'
    )
    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [user.email],
        fail_silently=False,
    )


def register_view(request):
    """Handle user registration with email verification."""
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data.get('email')
            
            # Check if email already exists (either in User or SocialAccount)
            if User.objects.filter(email=email).exists():
                messages.error(request, 'An account with this email already exists. Please use a different email or log in.')
                return render(request, 'asl_recognition/register.html', {'form': form})
            
            # Check if email is already used by a social account
            from allauth.socialaccount.models import SocialAccount
            if SocialAccount.objects.filter(extra_data__contains=email).exists():
                messages.error(request, 'This email is already associated with a social account. Please log in using Google or use a different email.')
                return render(request, 'asl_recognition/register.html', {'form': form})
            
            user = form.save(commit=False)
            user.is_active = False
            user.save()
            try:
                _send_verification_email(request, user)
                messages.success(request, 'Account created successfully! Check your email and verify before logging in.')
                return redirect('login')
            except Exception as e:
                user.delete()
                messages.error(request, 'Failed to send verification email. Please try again.')
                return redirect('register')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    else:
        form = RegisterForm()

    return render(request, 'asl_recognition/register.html', {'form': form})


def verify_email(request, token):
    signer = TimestampSigner()
    try:
        user_pk = signer.unsign(token, max_age=60 * 60 * 24)
        user = User.objects.get(pk=user_pk)
        if user.is_active:
            messages.info(request, 'Email already verified. Please log in.')
            return redirect('login')
        user.is_active = True
        user.save()
        messages.success(request, 'Email verified successfully. You can now log in.')
        return redirect('login')
    except SignatureExpired:
        messages.error(request, 'Verification link expired. Please register again.')
    except (BadSignature, User.DoesNotExist):
        messages.error(request, 'Invalid verification link.')
    return redirect('register')


def login_view(request):
    """Handle user login with email"""
    from django.contrib.auth import login
    
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            
            # Validate input
            if not email or not password:
                messages.error(request, 'Please enter both email and password.')
                return render(request, 'asl_recognition/login.html', {'form': form})
            
            # Find user by email
            try:
                user = User.objects.get(email=email)
                
                # Check if this is a social account (only if user has no usable password)
                # This is for Google/social auth users who registered via social login
                has_social_account = hasattr(user, 'socialaccount_set') and user.socialaccount_set.exists()
                has_no_password = not user.has_usable_password()
                
                # Only auto-login for social accounts with no password set
                if has_social_account and has_no_password and not password:
                    # This is a Google/social account without a password set
                    login(request, user, backend='django.contrib.auth.backends.ModelBackend')
                    messages.success(request, f'Welcome back, {user.username}!')
                    return redirect('home')
                else:
                    # Regular account - authenticate with password
                    print(f"DEBUG: Attempting to authenticate user: {user.username}")
                    print(f"DEBUG: User has_usable_password: {user.has_usable_password()}")
                    authenticated_user = authenticate(request, username=user.username, password=password)
                    print(f"DEBUG: authenticate() returned: {authenticated_user}")
                    
                    if authenticated_user is not None:
                        if not user.is_active:
                            messages.error(request, 'Please verify your email before logging in. Check your inbox for the verification link.')
                        else:
                            login(request, authenticated_user, backend='django.contrib.auth.backends.ModelBackend')
                            messages.success(request, f'Welcome back, {user.username}!')
                            return redirect('home')
                    else:
                        messages.error(request, 'Invalid password. Please check your password and try again.')
                        
            except User.DoesNotExist:
                messages.error(request, 'No account found with this email address. Please check your email or register for a new account.')
        else:
            # Form validation errors
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field.title()}: {error}')
    else:
        form = LoginForm()
        
    return render(request, 'asl_recognition/login.html', {'form': form})


def logout_view(request):
    """Handle user logout"""
    from django.contrib.auth import logout
    from django.contrib.sessions.models import Session
    
    # Clear all sessions for this user
    if request.user.is_authenticated:
        # Delete all sessions for this user to fix social login issues
        Session.objects.filter(session_key__in=list(request.session.keys())).delete()
        
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('index')


@login_required
def home(request):
    """Render the home page for authenticated users"""
    return render(request, 'asl_recognition/home.html')


def learn(request):
    """Render the ASL learning guide page"""
    from django.conf import settings
    context = {
        'DATASET_URL': getattr(settings, 'DATASET_URL', '/dataset/'),
        'GUIDE_URL': getattr(settings, 'GUIDE_URL', '/guide/')
    }
    return render(request, 'asl_recognition/learn.html', context)


def webcam_backup(request):
    """Render the webcam backup page with ASL recognition"""
    from django.conf import settings
    context = {
        'DATASET_URL': getattr(settings, 'DATASET_URL', '/dataset/'),
        'GUIDE_URL': getattr(settings, 'GUIDE_URL', '/guide/')
    }
    return render(request, 'asl_recognition/webcam_backup.html', context)


@login_required
def dashboard(request):
    """Render the main game dashboard for authenticated users"""
    # Get user's recent scores
    user_scores = GameScore.objects.filter(user=request.user)[:5]
    return render(request, 'asl_recognition/dashboard.html', {
        'user_scores': user_scores
    })


@login_required
def game(request):
    """Render the game page with ASL recognition"""
    from django.conf import settings
    context = {
        'DATASET_URL': getattr(settings, 'DATASET_URL', '/dataset/'),
        'GUIDE_URL': getattr(settings, 'GUIDE_URL', '/guide/')
    }
    return render(request, 'asl_recognition/game.html', context)


@login_required
def save_score(request):
    """API endpoint to save game score"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Only POST requests allowed'}, status=405)
    
    try:
        data = json.loads(request.body)
        score = data.get('score', 0)
        duration = data.get('duration', 300)
        game_mode = data.get('game_mode', 'standard')
        
        game_score = GameScore.objects.create(
            user=request.user,
            score=score,
            duration=duration,
            game_mode=game_mode
        )
        
        return JsonResponse({
            'success': True,
            'score_id': game_score.id,
            'message': 'Score saved successfully!'
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


def leaderboard(request):
    """Display top 10 highest scores with mode filter"""
    mode = request.GET.get('mode', 'standard')
    top_scores = GameScore.objects.select_related('user').prefetch_related('user__profile').filter(game_mode=mode)[:10]
    return render(request, 'asl_recognition/leaderboard.html', {
        'top_scores': top_scores,
        'current_mode': mode
    })


# Custom password reset views with timezone-unaware tokens
import hashlib
import datetime
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str

class SimplePasswordResetTokenGenerator:
    """Simple token generator that doesn't use timezone-aware datetimes"""
    
    def make_token(self, user):
        """Generate a simple token based on user data and timestamp"""
        # Use local naive datetime
        now = datetime.datetime.now()
        timestamp = int(now.timestamp())
        # Create token: user_pk + timestamp + hash
        data = f"{user.pk}:{timestamp}:{user.password}"
        token_hash = hashlib.sha256(data.encode()).hexdigest()[:20]
        return f"{timestamp}-{token_hash}"
    
    def check_token(self, user, token, timeout=3600):
        """Check if token is valid and not expired"""
        try:
            timestamp_str, token_hash = token.split('-')
            token_time = int(timestamp_str)
            now = int(datetime.datetime.now().timestamp())
            
            # Check expiration (default 1 hour)
            if now - token_time > timeout:
                return False
            
            # Verify hash matches - recreate with original timestamp
            data = f"{user.pk}:{token_time}:{user.password}"
            expected_hash = hashlib.sha256(data.encode()).hexdigest()[:20]
            return token_hash == expected_hash
        except (ValueError, AttributeError):
            return False


simple_token_generator = SimplePasswordResetTokenGenerator()


def custom_password_reset(request):
    """Custom password reset that sends email with simple token"""
    if request.method == 'POST':
        email = request.POST.get('email')
        try:
            user = User.objects.get(email=email)
            # Generate simple token
            token = simple_token_generator.make_token(user)
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            
            reset_url = request.build_absolute_uri(
                f'/accounts/password/reset/confirm/{uid}/{token}/'
            )
            
            subject = '[ASL Learning App] Password Reset'
            message = (
                f'Hi {user.username},\n\n'
                f'You requested a password reset. Click the link below to reset your password:\n'
                f'{reset_url}\n\n'
                f'This link will expire in 1 hour.\n\n'
                f'If you did not request this, please ignore this email.'
            )
            
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [email],
                fail_silently=False,
            )
            return render(request, 'account/password_reset_done.html')
        except User.DoesNotExist:
            # Don't reveal if email exists
            return render(request, 'account/password_reset_done.html')
    
    # Pre-fill email if provided in query string
    email_prefill = request.GET.get('email', '')
    return render(request, 'account/password_reset.html', {'email_prefill': email_prefill})


def custom_password_reset_confirm(request, uidb64, token):
    """Custom password reset confirmation with simple token validation"""
    import re
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None
    
    validlink = False
    error_message = None
    if user is not None and simple_token_generator.check_token(user, token):
        validlink = True
        if request.method == 'POST':
            password1 = request.POST.get('new_password1')
            password2 = request.POST.get('new_password2')
            
            # Validate password requirements
            if not password1 or len(password1) < 8:
                error_message = 'Password must be at least 8 characters long.'
            elif not re.search(r'[0-9]', password1):
                error_message = 'Password must contain at least one number.'
            elif not re.search(r'[!@#$%^&*()_+\-=\[\]{};:\"\\|,.<>\/?]', password1):
                error_message = 'Password must contain at least one special character (!@#$%^&*()_+-=[]{}|;:\"\\|,.<>/?).'
            elif password1 != password2:
                error_message = 'Passwords do not match.'
            
            if error_message:
                messages.error(request, error_message)
            else:
                user.set_password(password1)
                user.save()
                return render(request, 'account/password_reset_from_key_done.html')
    
    return render(request, 'account/password_reset_from_key.html', {
        'validlink': validlink,
        'form': {}  # Empty form for template compatibility
    })


@login_required
def profile_view(request):
    """Display and edit user profile"""
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    best_score = profile.get_best_score()
    
    if request.method == 'POST':
        form = ProfileForm(request.POST, request.FILES, instance=profile, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('profile')
    else:
        form = ProfileForm(instance=profile, user=request.user)
    
    context = {
        'form': form,
        'profile': profile,
        'best_score': best_score,
        'recent_scores': GameScore.objects.filter(user=request.user)[:5]
    }
    return render(request, 'asl_recognition/profile.html', context)


@login_required
def change_password_view(request):
    """Handle password change with email confirmation"""
    if request.method == 'POST':
        # Check if user confirmed the password change
        if 'confirm' in request.POST:
            # Get form data from session (stored during confirmation)
            form_data = request.session.get('password_change_form_data', {})
            form = CustomPasswordChangeForm(request.user, form_data)
            
            if form.is_valid():
                # Create a timestamped token for password change confirmation
                signer = TimestampSigner()
                token = signer.sign(f"{request.user.id}:{form.cleaned_data['new_password1']}")
                
                # Generate confirmation link
                confirmation_link = request.build_absolute_uri(f"/confirm-password-change/{token}/")
                
                # Send email with confirmation link
                try:
                    subject = '[ASL Learning App] Confirm Password Change'
                    
                    # Render HTML email template
                    html_message = render_to_string('email/password_change_confirmation.html', {
                        'username': request.user.username,
                        'confirmation_link': confirmation_link
                    })
                    
                    # Plain text fallback
                    message = (
                        f'Hi {request.user.username},\n\n'
                        f'You requested to change your password. Please click the link below to confirm this change:\n\n'
                        f'{confirmation_link}\n\n'
                        f'This link will expire in 1 hour for security reasons.\n\n'
                        f'If you did not request this change, please contact support immediately.\n\n'
                        f'Thank you for using ASL Learning App!'
                    )
                    
                    send_mail(
                        subject,
                        message,
                        settings.DEFAULT_FROM_EMAIL,
                        [request.user.email],
                        html_message=html_message,
                        fail_silently=False,
                    )
                    
                    # Clear session data
                    if 'password_change_form_data' in request.session:
                        del request.session['password_change_form_data']
                    
                    messages.success(request, 'Password change confirmation link has been sent to your email. Please check your inbox and click the link to complete the change.')
                except Exception as e:
                    messages.error(request, 'Failed to send confirmation email. Please try again.')
                
                return redirect('profile')
            else:
                # Form is invalid, show errors
                messages.error(request, 'Please correct the errors below.')
                return render(request, 'asl_recognition/change_password.html', {'form': form})
        else:
            # First form submission - validate and show confirmation
            form = CustomPasswordChangeForm(request.user, request.POST)
            if form.is_valid():
                # Store form data in session for confirmation step
                request.session['password_change_form_data'] = request.POST
                return render(request, 'asl_recognition/change_password_confirm.html')
            else:
                # Form is invalid, show errors
                messages.error(request, 'Please correct the errors below.')
                return render(request, 'asl_recognition/change_password.html', {'form': form})
    else:
        form = CustomPasswordChangeForm(request.user)
    
    return render(request, 'asl_recognition/change_password.html', {'form': form})


@login_required
def delete_profile_picture(request):
    """Delete user's profile picture"""
    profile = request.user.profile
    if profile.profile_picture:
        profile.profile_picture.delete()
        profile.save()
        messages.success(request, 'Profile picture removed successfully.')
    return redirect('profile')


def confirm_password_change(request, token):
    """Handle password change confirmation from email link"""
    try:
        signer = TimestampSigner()
        data = signer.unsign(token, max_age=3600)  # Token expires in 1 hour
        
        # Parse user_id and new_password from token
        user_id, new_password = data.split(':', 1)
        user = User.objects.get(id=user_id)
        
        # Change the password
        user.set_password(new_password)
        user.save()
        
        # Send notification email
        try:
            subject = '[ASL Learning App] Password Successfully Changed'
            
            # Render HTML email template
            html_message = render_to_string('email/password_changed_success.html', {
                'username': user.username,
                'login_link': request.build_absolute_uri('/login/')
            })
            
            # Plain text fallback
            message = (
                f'Hi {user.username},\n\n'
                f'Your password has been successfully changed.\n\n'
                f'If you did not make this change, please contact support immediately.\n\n'
                f'Thank you for using ASL Learning App!'
            )
            
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [user.email],
                html_message=html_message,
                fail_silently=False,
            )
        except Exception as e:
            pass  # Don't fail the password change if email fails
        
        messages.success(request, 'Your password has been successfully changed! Please log in with your new password.')
        return redirect('login')
        
    except (SignatureExpired, BadSignature, User.DoesNotExist, ValueError):
        messages.error(request, 'Invalid or expired password change link. Please try again.')
        return redirect('login')


@login_required
def view_user_profile(request, username):
    """View another user's profile"""
    try:
        user = User.objects.get(username=username)
        if user == request.user:
            return redirect('profile')
        
        profile = user.profile
        best_score = profile.get_best_score()
        
        context = {
            'profile_user': user,
            'profile': profile,
            'best_score': best_score,
            'recent_scores': GameScore.objects.filter(user=user)[:5],
            'is_own_profile': False
        }
        return render(request, 'asl_recognition/view_profile.html', context)
    except User.DoesNotExist:
        messages.error(request, 'User not found.')
        return redirect('leaderboard')


def admin_login(request):
    """Separate admin login that doesn't interfere with regular user sessions"""
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        # Validate input
        if not username or not password:
            messages.error(request, 'Please enter both username and password.')
            return render(request, 'admin/admin_login.html')
        
        # Authenticate user
        from django.contrib.auth import authenticate
        user = authenticate(request, username=username, password=password)
        
        if user is not None and (user.is_staff or user.is_superuser):
            # Check if user is active
            if not user.is_active:
                messages.error(request, 'Your admin account has been deactivated. Please contact the system administrator.')
                return render(request, 'admin/admin_login.html')
            
            # Use standard Django login - this will work with CSRF properly
            login(request, user)
            messages.success(request, f'Welcome back, {user.username}! Admin access granted.')
            return redirect('/admin/')
            
        else:
            # Check if user exists but wrong password
            try:
                user_obj = User.objects.get(username=username)
                
                if user_obj.is_staff or user_obj.is_superuser:
                    messages.error(request, 'Invalid password. Please try again.')
                else:
                    messages.error(request, 'This account does not have admin privileges.')
            except User.DoesNotExist:
                messages.error(request, 'Admin account not found. Please check your username.')
    
    return render(request, 'admin/admin_login.html')


def admin_logout(request):
    """Separate admin logout"""
    logout(request)
    messages.success(request, 'Admin logout successful!')
    return redirect('/admin/login/')
