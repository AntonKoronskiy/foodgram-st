from django.db import models
from django.core.validators import MinValueValidator
from users.models import User
# Create your models here.


class Ingredients(models.Model):
    name = models.CharField(
        verbose_name='Название', max_length=100, default='unknown',
    )
    measurement_unit = models.CharField(
        verbose_name='Единица измерения', max_length=70, default='г',
    )


class Recipe(models.Model):
    author = models.ForeignKey(
        User, verbose_name='Автор публикации',
        on_delete=models.CASCADE, related_name='recipes', default=1,
    )
    name = models.CharField(
        verbose_name='Название', max_length=200, default='unknown',
    )
    image = models.ImageField(
        verbose_name='Изображение блюда',
        upload_to='recipes/', null=True, blank=True,
    )
    text = models.TextField(
        verbose_name='Описание', max_length=200,
    )
    ingredients = models.ManyToManyField(
        Ingredients, verbose_name='Ингредиенты блюда', related_name='recipes',
    )
    cooking_time = models.IntegerField(
        verbose_name='Время приготовления', validators=[MinValueValidator(1)],
    )


class RecipeIngredient(models.Model):
    recipe = models.ForeignKey(
        Recipe, verbose_name='Рецепт',
        on_delete=models.CASCADE, related_name='recipe_ingredient',
    )
    ingredient = models.ForeignKey(
        Ingredients, verbose_name='Ингредиенты', on_delete=models.CASCADE,
    )
    amount = models.PositiveSmallIntegerField(
        verbose_name='Количество', validators=[MinValueValidator(1)],
    )

    def __str__(self):
        return f'Рецепт {self.recipe} содержит {self.ingredient}'


class Favorite(models.Model):
    user = models.ForeignKey(
        User, verbose_name='Пользователь',
        on_delete=models.CASCADE, related_name='favorites',
    )
    recipe = models.ForeignKey(
        Recipe, verbose_name='Рецепт',
        on_delete=models.CASCADE, related_name='favorited_by',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'recipe')
        verbose_name = 'Избранное'
        verbose_name_plural = 'Избранные рецепты'

    def __str__(self):
        return f'{self.user.username} - {self.recipe.name}'


class Subscription(models.Model):
    user = models.ForeignKey(
        User, verbose_name='Пользователь',
        on_delete=models.CASCADE, related_name='subscriptions'
    )
    author = models.ForeignKey(
        User, verbose_name='Автор',
        on_delete=models.CASCADE, related_name='subscribers'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'author')


class ShoppingCart(models.Model):
    user = models.ForeignKey(
        User, verbose_name='Пользователь', on_delete=models.CASCADE,
        related_name='shop_cart',
    )
    recipe = models.ForeignKey(
        Recipe, verbose_name='Рецепт', on_delete=models.CASCADE,
        related_name='in_shopping_cart',
    )
    data = models.DateTimeField(
        verbose_name='Дата добавления', auto_now_add=True, editable=False,
    )

    class Meta:
        verbose_name = 'Рецепт в корзине'
        verbose_name_plural = 'Рецепты в корзине'

    def __str__(self):
        return f'{self.recipe}'
