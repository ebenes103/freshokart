from django.contrib import admin
from .models import UserProfile, Category, Product, ProductImage, Cart, Chat

admin.site.register(UserProfile)
admin.site.register(Category)
admin.site.register(Product)
admin.site.register(ProductImage)
admin.site.register(Cart)
admin.site.register(Chat)