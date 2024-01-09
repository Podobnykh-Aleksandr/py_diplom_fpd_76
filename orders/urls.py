from django.urls import path

from orders.views import OrderView, PartnerOrders, BasketView


app_name = 'orders'

urlpatterns = [
    path('partner/orders', PartnerOrders.as_view(), name='partner-orders'),
    path('order', OrderView.as_view(), name='order'),
    path('basket', BasketView.as_view(), name='basket'),
]