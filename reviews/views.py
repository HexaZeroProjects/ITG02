from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect
from core.services import create_review  # Используем функцию из core

class AddReviewView(LoginRequiredMixin, View):
    """
    Представление для добавления нового отзыва через сервисный слой.
    """
    def post(self, request, product_id):
        review_text = request.POST.get('review_text')
        rating = int(request.POST.get('rating', 1))

        # Передаём данные в сервисный слой
        create_review(
            user=request.user,
            product_id=product_id,
            review_text=review_text,
            rating=rating
        )

        return redirect('product_detail', pk=product_id)
