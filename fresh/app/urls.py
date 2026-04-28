from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('signup/', views.signup, name='signup'),
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    path('seller-dashboard/', views.seller_dashboard, name='seller_dashboard'),
    path('all-products/', views.all_products, name='all_products'),
    path('product/<int:product_id>/', views.product_detail, name='product_detail'),  # This must exist
    path('cart/', views.cart_view, name='cart'),
    path('book-product/<int:product_id>/', views.book_product, name='book_product'),
    path('cancel-booking/<int:booking_id>/', views.cancel_booking, name='cancel_booking'),
    path('remove-from-cart/<int:cart_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('category/<int:category_id>/', views.category_products, name='category_products'),
    path('api/districts/', views.get_districts, name='get_districts'),
    path('api/cities/', views.get_cities, name='get_cities'),
    path('send-message/<int:product_id>/', views.send_message, name='send_message'),
    path('api/cart-count/', views.get_cart_count, name='get_cart_count'),
]