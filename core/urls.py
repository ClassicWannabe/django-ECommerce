from django.urls import path
from .views import (HomeView, 
                    ItemDetailView, 
                    CheckoutView,
                    PaymentView, 
                    product, 
                    add_to_cart, 
                    remove_from_cart, 
                    remove_single_item_from_cart, 
                    OrderSummaryView,
                    AddCouponView,
                    RequestRefundView)

app_name = 'core'

urlpatterns = [
    path('', HomeView.as_view(), name='item-list_url'),
    path('checkout', CheckoutView.as_view(), name='checkout_url'),
    path('order-summary', OrderSummaryView.as_view(), name='order-summary_url'),
    path('product/<slug>', ItemDetailView.as_view(), name='product_url'),
    path('add-product/<slug>', add_to_cart, name='add-product_url'),
    path('add-coupon/', AddCouponView.as_view(), name='add-coupon_url'),
    path('remove-product/<slug>', remove_from_cart, name='remove-product_url'),
    path('remove-single-product/<slug>', remove_single_item_from_cart, name='remove-single-product_url'),
    path('payment/<payment_option>',PaymentView.as_view(),name='payment_url'),
    path('request-refund',RequestRefundView.as_view(),name='request-refund_url')
]
