from django.urls import path, include
from .views import (recipes_list, get_recipe, ingredients_list,
                    get_ingredient, short_url_recipe, add_favorite,
                    shopping_cart, download_shopping_cart,
                    UsersViewSet)
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register(r'users', UsersViewSet, 'user')


urlpatterns = [
    path('', include(router.urls)),
    path('recipes/', recipes_list, name='recipes-list'),
    path('recipes/<int:id>/', get_recipe, name='get-recipe'),
    path('recipes/<int:id>/shopping_cart/', shopping_cart,
         name='shopping-cart'),
    path('recipes/download_shopping_cart/', download_shopping_cart,
         name="download-shopping-cart"),
    path('recipes/<int:id>/get-link/', short_url_recipe, name='short-link'),
    path('recipes/<int:id>/favorite/', add_favorite, name='favorite'),
    path('ingredients/', ingredients_list, name='ingredients-list'),
    path('ingredients/<int:id>/', get_ingredient,
         name='get-ingredients'),
]
