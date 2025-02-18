from django.views.generic.edit import CreateView
from django.contrib.auth import views as auth_views
from django.urls import reverse_lazy
from django.contrib.auth.models import User
from .forms import CustomUserCreationForm, CustomPasswordResetForm, CustomSetPasswordForm
from django.views.generic.edit import UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from .models import UserProfile
from .forms import UserProfileForm


class RegisterView(CreateView):
    form_class = CustomUserCreationForm
    template_name = 'users/register.html'
    success_url = reverse_lazy('login')


class CustomPasswordResetView(auth_views.PasswordResetView):
    form_class = CustomPasswordResetForm
    template_name = 'users/password_reset.html'
    success_url = reverse_lazy('password_reset_done')


class CustomPasswordResetDoneView(auth_views.PasswordResetDoneView):
    template_name = 'users/password_reset_done.html'


class CustomPasswordResetConfirmView(auth_views.PasswordResetConfirmView):
    form_class = CustomSetPasswordForm
    template_name = 'users/password_reset_confirm.html'
    success_url = reverse_lazy('password_reset_complete')


class CustomPasswordResetCompleteView(auth_views.PasswordResetCompleteView):
    template_name = 'users/password_reset_complete.html'


from django.shortcuts import redirect
from django.contrib.auth.views import LoginView

class CustomLoginView(LoginView):
    """
    Кастомное представление для входа, чтобы перенаправлять пользователей в зависимости от их статуса.
    """
    template_name = 'users/login.html'  # Укажите путь к вашему шаблону логина

    def get_success_url(self):
        user = self.request.user
        # Перенаправление администратора
        if user.is_staff or user.is_superuser:
            return '/analytics/'  # URL аналитики
        # Перенаправление обычного пользователя
        return '/'  # Главная страница




class ProfileView(LoginRequiredMixin, UpdateView):
    model = UserProfile
    form_class = UserProfileForm
    template_name = 'users/profile.html'
    success_url = reverse_lazy('profile')

    def get_object(self):
        return self.request.user.profile

    def form_valid(self, form):
        response = super().form_valid(form)
        form.save()  # Явно сохраняем изменения
        return response



from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from core.services_bot import bind_telegram_service

@csrf_exempt
def bind_telegram(request):
    if request.method == "POST":
        data = json.loads(request.body)
        email = data.get("email")
        telegram_id = data.get("telegram_id")

        result = bind_telegram_service(email, telegram_id)
        return JsonResponse(result)

    return JsonResponse({"status": "error", "message": "Неверный метод запроса"})
