from django.urls import path, include
from rest_framework.routers import DefaultRouter

from shops.views import ProductInfoView, CategoryView, ShopView, SellerUpdateCatalog, SellerState

app_name = 'shops'
router = DefaultRouter()
router.register(r'products', ProductInfoView, basename='products')

urlpatterns = [
    path('categories', CategoryView.as_view(), name='categories'),
    path('shops', ShopView.as_view(), name='shops'),
    path('seller/update', SellerUpdateCatalog.as_view(), name='partner-update'),
    path('seller/state', SellerState.as_view(), name='partner-state'),
    path('', include(router.urls)),
    ]