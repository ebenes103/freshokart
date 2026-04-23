from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta

class UserProfile(models.Model):
    USER_TYPE_CHOICES = (
        ('buyer', 'Buyer'),
        ('seller', 'Seller'),
    )
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    user_type = models.CharField(max_length=10, choices=USER_TYPE_CHOICES)
    phone = models.CharField(max_length=15)
    address = models.TextField()
    district = models.CharField(max_length=100)
    city = models.CharField(max_length=100)
    
    def __str__(self):
        return f"{self.user.username} - {self.user_type}"

class Category(models.Model):
    name = models.CharField(max_length=50)
    icon = models.ImageField(upload_to='category_icons/', null=True, blank=True)
    
    def __str__(self):
        return self.name

class Product(models.Model):
    seller = models.ForeignKey(UserProfile, on_delete=models.CASCADE, limit_choices_to={'user_type': 'seller'})
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    name = models.CharField(max_length=200)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.IntegerField()
    unit = models.CharField(max_length=20, choices=[
        ('kg', 'Kilogram'),
        ('dozen', 'Dozen'),
        ('piece', 'Piece'),
        ('packet', 'Packet'),
    ])
    district = models.CharField(max_length=100)
    city = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    expiry_date = models.DateTimeField()
    is_available = models.BooleanField(default=True)
    booked_by = models.ForeignKey(UserProfile, on_delete=models.SET_NULL, null=True, blank=True, related_name='booked_products')
    
    def save(self, *args, **kwargs):
        if not self.expiry_date:
            self.expiry_date = timezone.now() + timedelta(days=3)
        super().save(*args, **kwargs)
    
    def is_fresh(self):
        return timezone.now() <= self.expiry_date
    
    def __str__(self):
        return f"{self.name} - {self.seller.user.username}"

class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='products/')
    
    def __str__(self):
        return f"Image for {self.product.name}"

class Cart(models.Model):
    buyer = models.ForeignKey(UserProfile, on_delete=models.CASCADE, limit_choices_to={'user_type': 'buyer'})
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.IntegerField(default=1)
    added_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('buyer', 'product')
    
    def __str__(self):
        return f"{self.buyer.user.username} - {self.product.name}"

class Chat(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    buyer = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='buyer_chats')
    seller = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='seller_chats')
    message = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)
    
    def __str__(self):
        return f"Chat about {self.product.name}"