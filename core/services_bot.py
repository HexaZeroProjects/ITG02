from django.contrib.auth import get_user_model

User = get_user_model()

def bind_telegram_service(email, telegram_id):
    """
    Привязывает Telegram ID к профилю пользователя.
    """
    user = User.objects.filter(email=email).first()
    if user and hasattr(user, 'profile'):
        user.profile.telegram_id = telegram_id
        user.profile.save()
        return {"status": "success", "message": "Telegram ID привязан"}
    return {"status": "error", "message": "Пользователь не найден или профиль отсутствует"}
