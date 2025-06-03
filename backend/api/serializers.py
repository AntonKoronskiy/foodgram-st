from rest_framework import serializers
from recipe.models import (Recipe, Ingredients, Favorite, Subscription,
                           RecipeIngredient, ShoppingCart)
from users.models import User
from drf_extra_fields.fields import Base64ImageField
from django.core.validators import MinValueValidator, MaxValueValidator


MIN_VALUE_VALIDATE = 1
MAX_VALUE_VALIDATE = 32000


class UserSerializer(serializers.ModelSerializer):
    is_subscribed = serializers.SerializerMethodField()
    avatar = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ('id', 'username', 'first_name', 'last_name',
                  'email', 'is_subscribed', 'avatar')
        extra_kwargs = {'password': {'write_only': True}}

    def get_is_subscribed(self, obj):
        request = self.context['request']
        user = request.user

        if (request and not user.is_anonymous):
            return user.subscriptions.filter(author=obj).exists()
        return False

    def get_avatar(self, obj):
        request = self.context.get('request')
        if obj.avatar and hasattr(obj.avatar, 'url'):
            return request.build_absolute_uri(obj.avatar.url)
        return None


class RecipeShortLinkSerializer(serializers.ModelSerializer):
    image = serializers.ImageField()

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')
        read_only_fields = fields


class AvatarSerializer(serializers.ModelSerializer):
    avatar = Base64ImageField(required=True)

    class Meta:
        model = User
        fields = ('avatar',)


class UserSubscribeSerializer(UserSerializer):
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()
    is_subscribed = serializers.SerializerMethodField()
    avatar = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ('id', 'username', 'first_name', 'last_name', 'email',
                  'is_subscribed', 'avatar', 'recipes_count', 'recipes')
        read_only_fields = fields

    def get_is_subscribed(self, obj):
        request = self.context['request']
        user = request.user
        if user.is_anonymous:
            return False
        return obj.subscribers.filter(user=user).exists()

    def get_recipes_count(self, obj):
        return obj.recipes.count()

    def get_recipes(self, obj):
        request = self.context.get('request')
        recipes_limit = request.query_params.get('recipes_limit')
        queryset = obj.recipes.all()
        if recipes_limit is not None and recipes_limit.isdigit():
            queryset = queryset[:int(recipes_limit)]
        return RecipeShortLinkSerializer(queryset, many=True,
                                         context={'request': request}).data

    def get_avatar(self, obj):
        request = self.context.get('request')
        if obj.avatar and hasattr(obj.avatar, 'url'):
            return request.build_absolute_uri(obj.avatar.url)
        return None


class SubscribeCreateSerializer(serializers.Serializer):
    def validate(self, data):
        request = self.context['request']
        author = self.context['author']
        user = request.user

        if user == author:
            raise serializers.ValidationError(
                'Нельзя подписаться на себя')

        if author in user.subscriptions.values_list('author', flat=True):
            raise serializers.ValidationError('Подписка уже существует')

        return data


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredients
        fields = ('id', 'name', 'measurement_unit')
        read_only_fields = fields


class RecipeIngredientSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField(source='ingredient.id')
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit')

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'name', 'measurement_unit', 'amount')


class IngredientsDetailSerializer(serializers.ModelSerializer):
    id = serializers.PrimaryKeyRelatedField(queryset=Ingredients.objects.all())
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit')
    amount = serializers.IntegerField(
        validators=[
            MinValueValidator(MIN_VALUE_VALIDATE),
            MaxValueValidator(MAX_VALUE_VALIDATE),],
    )

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'name', 'measurement_unit', 'amount')


class ForChangeRecipeSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)
    ingredients = IngredientsDetailSerializer(many=True)
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()
    image = Base64ImageField(required=True)
    cooking_time = serializers.IntegerField(
        validators=[
            MinValueValidator(MIN_VALUE_VALIDATE),
            MaxValueValidator(MAX_VALUE_VALIDATE),],
    )

    class Meta:
        model = Recipe
        fields = ('id', 'author', 'ingredients', 'is_favorited',
                  'is_in_shopping_cart', 'name', 'image', 'text',
                  'cooking_time')
        extra_kwargs = {'name': {'required': True, 'allow_null': False},
                        'image': {'required': True, 'allow_null': False}}

    def validate(self, data):
        ingredients = data.get('ingredients')

        if not ingredients:
            raise serializers.ValidationError(
                'Поле ингредиентов является обязательным'
            )
        return data

    def validate_ingredients(self, value):
        if not value:
            raise serializers.ValidationError(
                'Список ингредиентов не может быть пустым')
        ingredients_ids = set()
        for i in value:
            ingredient = i.get('id')
            if ingredient in ingredients_ids:
                raise serializers.ValidationError(
                    'В рецепте не должно быть повторяющихся ингредиентов')
            ingredients_ids.add(ingredient)

        return value

    def validate_image(self, value):
        if not value:
            raise serializers.ValidationError(
                'Поле изображения не может быть пустым')
        return value

    def get_ingredients(self, obj):
        ingredients = obj.recipe_ingredient.all()
        return IngredientsDetailSerializer(ingredients, many=True).data

    def create_ingredients(self, recipe, ingredients_list):
        ingredients = []
        for i in ingredients_list:
            ingredients.append(
                RecipeIngredient(
                    recipe=recipe,
                    ingredient=i['id'],
                    amount=i['amount'],
                )
            )
        RecipeIngredient.objects.bulk_create(ingredients)

    def create(self, validated_data):
        ingredients_list = validated_data.pop('ingredients')
        validated_data.pop('author', None)
        recipe = Recipe.objects.create(author=self.context['request'].user,
                                       **validated_data)
        self.create_ingredients(recipe, ingredients_list)
        return recipe

    def update(self, instance, validated_data):
        ingredients_list = validated_data.pop('ingredients')

        if ingredients_list is not None:
            instance.recipe_ingredient.all().delete()
            self.create_ingredients(instance, ingredients_list)

        return super().update(instance, validated_data)

    def get_is_favorited(self, obj):
        request = self.context.get('request')
        if not request or request.user.is_anonymous:
            return False
        return obj.favorited_by.filter(user=request.user).exists()

    def get_is_in_shopping_cart(self, obj):
        request = self.context.get('request')
        if request is None or not request.user.is_authenticated:
            return False
        return obj.in_cart.filter(user=request.user).exists()


class ForReadRecipeSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)
    ingredients = RecipeIngredientSerializer(many=True,
                                             read_only=True,
                                             source='recipe_ingredient')
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = ('id', 'author', 'ingredients', 'is_favorited',
                  'is_in_shopping_cart', 'name', 'image', 'text',
                  'cooking_time')
        read_only_fields = fields

    def get_is_favorited(self, obj):
        request = self.context.get('request')
        if not request or request.user.is_anonymous:
            return False
        return obj.favorited_by.filter(user=request.user).exists()
    
    def get_is_in_shopping_cart(self, obj):
        request = self.context.get('request')
        if request is None or not request.user.is_authenticated:
            return False
        return obj.in_cart.filter(user=request.user).exists()
