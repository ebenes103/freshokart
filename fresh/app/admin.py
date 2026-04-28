from django.contrib import admin
from .models import UserProfile, Category, Product, ProductImage, Cart, Booking, Chat, District, City

admin.site.register(UserProfile)
admin.site.register(Category)
admin.site.register(Product)
admin.site.register(ProductImage)
admin.site.register(Cart)
admin.site.register(Booking)
admin.site.register(Chat)
admin.site.register(District)
admin.site.register(City)