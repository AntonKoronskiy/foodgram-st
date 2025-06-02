from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import (Recipe, Ingredients, RecipeIngredient,
                     Favorite, Subscription, ShoppingCart)
from users.models import User


# Register your models here.
@admin.register(User)
class UsersAdmin(UserAdmin):
    list_display = (
        'first_name', 'last_name',
        'username', 'email', 'is_staff'
    )
    search_fields = (
        'email', 'username',
    )


class Inlines(admin.TabularInline):
    model = RecipeIngredient
    extra = 1


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = (
        'name', 'author', 'favorite_count'
    )
    search_fields = (
        'name', 'author__username',
    )
    inlines = [Inlines]
    list_filter = ('cooking_time',)

    def favorite_count(self, obj):
        return obj.favorited_by.count()


@admin.register(Ingredients)
class IngredientsAdmin(admin.ModelAdmin):
    list_display = (
        'name', 'measurement_unit'
    )
    search_fields = (
        'name',
    )
    list_filter = (
        'measurement_unit',
    )


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = (
        'user', 'recipe',
    )
    search_fields = (
        'user__username', 'recipe__name'
    )


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = (
        'user', 'author',
    )
    search_fields = (
        'user__username', 'author__username'
    )


@admin.register(ShoppingCart)
class ShoppingCartAdmin(admin.ModelAdmin):
    list_display = (
        'user', 'recipe',
    )
    search_fields = (
        'user__username', 'recipe__name'
    )
