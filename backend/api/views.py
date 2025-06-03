from django.shortcuts import get_object_or_404
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import (IsAuthenticated,
                                        IsAuthenticatedOrReadOnly,
                                        AllowAny)
from djoser.views import UserViewSet
from djoser.serializers import UserCreateSerializer
from django.http import HttpResponse
from django.urls import reverse

from recipe.models import (Recipe, Ingredients, Favorite, Subscription,
                           ShoppingCart)
from .serializers import (IngredientSerializer, ForReadRecipeSerializer,
                          UserSerializer, UserSubscribeSerializer,
                          ForChangeRecipeSerializer, AvatarSerializer,
                          RecipeShortLinkSerializer, SubscribeCreateSerializer)
from users.models import User
from .pagination import CustomPaginator
from .filters import filter_recipes_by_params


class UsersViewSet(UserViewSet):
    queryset = User.objects.all()

    def get_permissions(self):
        if self.action in ['list', 'retrieve', 'create']:
            return [AllowAny()]
        return [IsAuthenticated()]

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = UserSerializer(page, many=True,
                                        context={'request': request})
            return self.get_paginated_response(serializer.data)

        serializer = UserSerializer(queryset, many=True,
                                    context={'request': request})
        return Response(serializer.data)

    def create(self, request, *args, **kwargs):
        self.serializer_class = UserCreateSerializer
        return super().create(request, *args, **kwargs)

    def retrieve(self, request, id=None):
        user = get_object_or_404(User, pk=id)
        serializer = UserSerializer(user, context={'request': request})
        return Response(serializer.data)

    @action(detail=False, methods=['get'],
            permission_classes=[IsAuthenticated])
    def me(self, request):
        serializer = UserSerializer(request.user, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post', 'delete'],
            url_path='subscribe', permission_classes=[IsAuthenticated])
    def subscribe(self, request, id=None):
        author = get_object_or_404(User, pk=id)
        user = request.user

        if request.method == 'POST':
            serializer = SubscribeCreateSerializer(
                data=request.data,
                context={'request': request,
                         'author': author})
            serializer.is_valid(raise_exception=True)

            subscription = Subscription.objects.create(user=user,
                                                       author=author)
            serializer = UserSubscribeSerializer(author,
                                                 context={'request': request})
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        subscription = user.subscriptions.filter(author=author).first()

        if not subscription:
            return Response(
                {'errors': 'Подписка не нейдена'},
                status=status.HTTP_400_BAD_REQUEST
            )

        subscription.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=['put', 'delete'], url_path='me/avatar')
    def avatar_update(self, request):
        if request.method == 'PUT':
            serializer = AvatarSerializer(request.user, data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)

        request.user.avatar.delete()
        request.user.avatar = None
        request.user.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=['get'], url_path='subscriptions')
    def subscriptions(self, request):
        subscription = request.user.subscriptions.all()

        authors = []
        for sub in subscription:
            authors.append(sub.author)
        obj = self.paginate_queryset(authors)
        if obj is not None:
            serializer = UserSubscribeSerializer(obj, many=True,
                                                 context={'request': request})
            return self.get_paginated_response(serializer.data)

        serializer = UserSubscribeSerializer(authors, many=True,
                                             context={'request': request})
        return Response(serializer.data)


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticatedOrReadOnly])
def recipes_list(request):

    if request.method == 'POST':
        if not request.user.is_authenticated:
            return Response(status=status.HTTP_401_UNAUTHORIZED)

        serializer = ForChangeRecipeSerializer(data=request.data,
                                               context={'request': request})
        serializer.is_valid(raise_exception=True)
        recipe = serializer.save(author=request.user)
        response_serializer = ForChangeRecipeSerializer(
            recipe, context={'request': request})
        return Response(response_serializer.data,
                        status=status.HTTP_201_CREATED)

    recipes = Recipe.objects.all().order_by('id')

    recipes = filter_recipes_by_params(recipes, request)

    paginator = CustomPaginator()
    result_page = paginator.paginate_queryset(recipes, request)
    serializer = ForReadRecipeSerializer(result_page, many=True,
                                         context={'request': request})
    return paginator.get_paginated_response(serializer.data)


@api_view(['GET', 'PATCH', 'DELETE'])
@permission_classes([IsAuthenticatedOrReadOnly])
def get_recipe(request, id):
    recipe = get_object_or_404(Recipe, id=id)

    if request.method == 'PATCH':
        serializer = ForChangeRecipeSerializer(recipe, data=request.data,
                                               partial=True,
                                               context={'request': request})
        if request.user.is_authenticated and request.user != recipe.author:
            return Response(status=status.HTTP_403_FORBIDDEN)

        if not request.user.is_authenticated:
            return Response(status=status.HTTP_401_UNAUTHORIZED)

        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)

    if request.method == 'DELETE':
        if not request.user.is_authenticated:
            return Response(status=status.HTTP_401_UNAUTHORIZED)

        if request.user.is_authenticated and request.user != recipe.author:
            return Response(status=status.HTTP_403_FORBIDDEN)

        recipe.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    serializer = ForReadRecipeSerializer(recipe, context={'request': request})
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticatedOrReadOnly])
def short_url_recipe(request, id):
    recipe = get_object_or_404(Recipe, id=id)
    url = reverse('short-link', args=[recipe.id])

    absolute_url = request.build_absolute_uri(url)
    full_url = absolute_url.replace('api/', '').replace('get-link/', '')

    return Response(data={'short-link': full_url}, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def download_shopping_cart(request):
    cart = request.user.shop_cart.select_related('recipe')

    if not cart.exists():
        return Response({'error':
                         'Корзина пустая'},
                        status=status.HTTP_400_BAD_REQUEST)

    information = []
    for rec in cart:
        recipe = rec.recipe
        information.append(f'-- {recipe.name}')
        information.append('Ингредиенты:')

        for q in recipe.recipe_ingredient.all():
            i = q.ingredient
            information.append(
                f'-{i.name}: {q.amount} {i.measurement_unit}'
            )

        information.append('')

    response = HttpResponse('\n'.join(information), content_type='text/plain')
    return response


@api_view(['POST', 'DELETE'])
@permission_classes([IsAuthenticated])
def shopping_cart(request, id):
    recipe = get_object_or_404(Recipe, id=id)
    if request.method == 'POST':
        if request.user.shop_cart.filter(recipe=recipe).exists():
            return Response({'error':
                             'Рецепт уже добавлен в корзину'},
                            status=status.HTTP_400_BAD_REQUEST)

        ShoppingCart.objects.create(user=request.user, recipe=recipe)
        serializer = RecipeShortLinkSerializer(recipe,
                                               context={'request': request})
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    shopping_cart = request.user.shop_cart.filter(recipe=recipe)
    if shopping_cart.exists():
        shopping_cart.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    return Response(status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST', 'DELETE'])
@permission_classes([IsAuthenticated])
def add_favorite(request, id):
    recipe = get_object_or_404(Recipe, pk=id)
    if request.method == 'POST':
        if request.user.favorites.filter(recipe=recipe).exists():
            return Response({'error':
                             'Рецепт уже добавлен в избранное'},
                            status=status.HTTP_400_BAD_REQUEST)

        Favorite.objects.create(user=request.user, recipe=recipe)
        serializer = RecipeShortLinkSerializer(recipe,
                                               context={'request': request})
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    favorite = request.user.favorites.filter(recipe=recipe)
    if favorite.exists():
        favorite.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    return Response(status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([AllowAny])
def ingredients_list(request):
    name = request.query_params.get('name')

    if name:
        ingredients = Ingredients.objects.filter(name__istartswith=name)
    else:
        ingredients = Ingredients.objects.all()

    serializer = IngredientSerializer(ingredients, many=True)

    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['GET'])
def get_ingredient(request, id):
    ingredient = get_object_or_404(Ingredients, id=id)
    serializer = IngredientSerializer(ingredient)
    return Response(serializer.data, status=status.HTTP_200_OK)
