from recipe.models import Favorite, ShoppingCart


def filter_recipes_by_params(queryset, request):
    user = request.user
    author_id = request.query_params.get('author')
    if author_id:
        queryset = queryset.filter(author__id=author_id)

    is_favorited = request.query_params.get('is_favorited')
    if is_favorited and str(is_favorited) == '1':
        if user.is_authenticated:
            favorite_ids = Favorite.objects.filter(
                user=user).values_list('recipe', flat=True)
            queryset = queryset.filter(id__in=favorite_ids)
        else:
            return queryset.none()

    is_in_shopping_cart = request.query_params.get('is_in_shopping_cart')
    if is_in_shopping_cart and str(is_in_shopping_cart) == '1':
        if user.is_authenticated:
            cart_ids = ShoppingCart.objects.filter(
                user=user).values_list('recipe', flat=True)
            queryset = queryset.filter(id__in=cart_ids)
        else:
            return queryset.none()

    return queryset
