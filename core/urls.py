from django.urls import path
from .views import (AddCouponView, HomeView, ItemDetailView, PaymentView, add_to_cart, checkoutView, products, remove_from_cart,OrderSummaryView,remove_single_item_from_cart,RequestRefundView)

app_name = 'core'

urlpatterns = [
    path('', HomeView.as_view(), name='home'),
    path('order_summary/', OrderSummaryView.as_view(),name='order_summary'),
    path('products/<slug>/', ItemDetailView.as_view(), name='products'),
    path('products/', products ,name='products'),
    path('add_to_cart/<slug>/', add_to_cart, name='add_to_cart'),
    path('add_coupon/', AddCouponView.as_view(), name='add_coupon'),
    path('remove_from_cart/<slug>/', remove_from_cart, name='remove_from_cart'),
    path('checkoutView/',checkoutView.as_view(),name='checkoutView'),
    path('remove_single_item_from_cart/<slug>/',remove_single_item_from_cart,name='remove_single_item_from_cart'),
    path('payment/<payment_option>/', PaymentView.as_view(),name='payment'),
    path('request_refund/',RequestRefundView.as_view(),name='request_refund')
]
