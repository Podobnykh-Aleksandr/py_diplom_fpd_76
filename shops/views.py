from django.core.exceptions import ValidationError
from django.core.validators import URLValidator
from django.http import JsonResponse
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.throttling import UserRateThrottle, AnonRateThrottle
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet
from rest_framework.response import Response

from shops.models import Category, Shop, ProductInfo, ProductParameter, Parameter, Product
from shops.permissions import IsShopUser
from shops.serializers import ShopSerializer, CategorySerializer, ProductInfoSerializer
from yaml import load as load_yaml, Loader
import requests
from distutils.util import strtobool


class CategoryView(ListAPIView):
    """Класс для просмотра категорий"""

    queryset = Category.objects.filter(shops__state=True)
    serializer_class = CategorySerializer


class ShopView(ListAPIView):
    """Класс для просмотра списка магазинов"""

    queryset = Shop.objects.filter(state=True)
    serializer_class = ShopSerializer


class ProductInfoView(ModelViewSet):
    """Класс для поиска товаров"""

    throttle_classes = [UserRateThrottle, AnonRateThrottle]

    queryset = ProductInfo.objects.filter(shop__state=True).select_related(
        'shop', 'product__category'
    ).prefetch_related('product_parameters__parameter').distinct()

    serializer_class = ProductInfoSerializer

    filter_backends = (DjangoFilterBackend,)
    filter_fields = ('product__name', 'shop_id', 'product__category_id')


class SellerUpdateCatalog(APIView):
    """Класс для обновления каталога от продавца"""

    permission_classes = [IsAuthenticated, IsShopUser]

    def post(self, request, *args, **kwargs):
        url = request.data.get('url')

        if url:
            validate_url = URLValidator()

            try:
                validate_url(url)
            except ValidationError as e:
                return JsonResponse({'Status': False, 'Error': str(e)})
            else:
                stream = requests.get(url).content
                data = load_yaml(stream, Loader=Loader)

                # Если у пользователя нет магазина - создать
                if not Shop.objects.filter(user_id=request.user.id).exists():
                    shop = Shop.objects.create(name=data['shop'], user_id=request.user.id)
                # Иначе получить магазин
                else:
                    shop = Shop.objects.get(user_id=request.user.id)

                # И обновить название
                shop.name = data['shop']
                shop.save()

                for category in data['categories']:
                    if not Category.objects.filter(id=category['id']).exists():
                        category_object = Category.objects.create(id=category['id'], name=category['name'])
                    else:
                        category_object = Category.objects.get(id=category['id'])

                    category_object.shops.add(shop.id)
                    category_object.save()

                ProductInfo.objects.filter(shop_id=shop.id).delete()

                for item in data['goods']:
                    product, _ = Product.objects.get_or_create(name=item['name'], category_id=item['category'])

                    product_info = ProductInfo.objects.create(product_id=product.id,
                                                              external_id=item['id'],
                                                              model=item['model'],
                                                              price=item['price'],
                                                              price_rrc=item['price_rrc'],
                                                              quantity=item['quantity'],
                                                              shop_id=shop.id)

                    for name, value in item['parameters'].items():
                        parameter_object, _ = Parameter.objects.get_or_create(name=name)
                        ProductParameter.objects.create(product_info_id=product_info.id,
                                                        parameter_id=parameter_object.id,
                                                        value=value)

                return JsonResponse({'Status': True})

        return JsonResponse({'Status': False, 'Errors': 'Не указаны все необходимые аргументы'})


class SellerState(APIView):
    """Класс для работы со статусом продавца"""

    permission_classes = [IsAuthenticated, IsShopUser]

    # Получить текущий статус
    def get(self, request, *args, **kwargs):
        shop = request.user.shop
        serializer = ShopSerializer(shop)
        return Response(serializer.data)

    # Изменить текущий статус
    def post(self, request, *args, **kwargs):
        state = request.data.get('state')

        if state:
            try:
                Shop.objects.filter(user_id=request.user.id).update(state=strtobool(state))
                return JsonResponse({'Status': True})
            except ValueError as error:
                return JsonResponse({'Status': False, 'Errors': str(error)})

        return JsonResponse({'Status': False, 'Errors': 'Не указаны все необходимые аргументы'})