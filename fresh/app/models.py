from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta

# =========================================
# LOCATION MODELS (Must be defined first)
# =========================================

class District(models.Model):
    name = models.CharField(max_length=100, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name
    
    class Meta:
        ordering = ['name']


class City(models.Model):
    district = models.ForeignKey(District, on_delete=models.CASCADE, related_name='cities')
    name = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.name} ({self.district.name})"
    
    class Meta:
        verbose_name_plural = "Cities"
        ordering = ['name']
        unique_together = ['district', 'name']


# =========================================
# USER PROFILE MODEL
# =========================================

class UserProfile(models.Model):
    USER_TYPE_CHOICES = (
        ('buyer', 'Buyer'),
        ('seller', 'Seller'),
    )
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    user_type = models.CharField(max_length=10, choices=USER_TYPE_CHOICES)
    phone = models.CharField(max_length=15)
    address = models.TextField()
    district = models.ForeignKey(District, on_delete=models.SET_NULL, null=True, blank=True)
    city = models.ForeignKey(City, on_delete=models.SET_NULL, null=True, blank=True)
    
    def __str__(self):
        return f"{self.user.username} - {self.user_type}"


# =========================================
# CATEGORY MODEL
# =========================================

class Category(models.Model):
    name = models.CharField(max_length=50)
    icon = models.ImageField(upload_to='category_icons/', null=True, blank=True)
    
    def __str__(self):
        return self.name


# =========================================
# PRODUCT MODEL
# =========================================

class Product(models.Model):
    UNIT_CHOICES = [
        ('kg', 'Kilogram'),
        ('dozen', 'Dozen'),
        ('piece', 'Piece'),
        ('packet', 'Packet'),
    ]
    
    seller = models.ForeignKey(UserProfile, on_delete=models.CASCADE, limit_choices_to={'user_type': 'seller'})
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    name = models.CharField(max_length=200)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity_available = models.IntegerField(default=1)
    quantity_booked = models.IntegerField(default=0)
    unit = models.CharField(max_length=20, choices=UNIT_CHOICES)
    district = models.ForeignKey(District, on_delete=models.SET_NULL, null=True)
    city = models.ForeignKey(City, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def quantity_left(self):
        """Return remaining quantity available"""
        return self.quantity_available - self.quantity_booked
    
    def is_available(self):
        """Check if product has any quantity left"""
        return self.quantity_left() > 0
    
    def is_fresh(self):
        """Check if product is fresh (within 3 days)"""
        days_old = (timezone.now() - self.created_at).days
        return days_old <= 3
    
    def is_moderately_fresh(self):
        """Check if product is moderately fresh (3-5 days)"""
        days_old = (timezone.now() - self.created_at).days
        return 3 < days_old <= 5
    
    def is_old(self):
        """Check if product is old (5+ days)"""
        days_old = (timezone.now() - self.created_at).days
        return days_old > 5
    
    def get_freshness_badge(self):
        """Return freshness badge type"""
        if self.is_fresh():
            return 'fresh'
        elif self.is_moderately_fresh():
            return 'moderate'
        else:
            return 'old'
    
    def __str__(self):
        return f"{self.name} - {self.seller.user.username}"


# =========================================
# PRODUCT IMAGE MODEL
# =========================================

class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='products/')
    
    def __str__(self):
        return f"Image for {self.product.name}"


# =========================================
# BOOKING MODEL
# =========================================

class Booking(models.Model):
    STATUS_CHOICES = (
        ('active', 'Active'),
        ('cancelled', 'Cancelled'),
        ('completed', 'Completed'),
    )
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='bookings')
    buyer = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='bookings')
    quantity = models.IntegerField(default=1)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    booked_at = models.DateTimeField(auto_now_add=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return f"Booking: {self.product.name} by {self.buyer.user.username}"


# =========================================
# CART MODEL
# =========================================

class Cart(models.Model):
    buyer = models.ForeignKey(UserProfile, on_delete=models.CASCADE, limit_choices_to={'user_type': 'buyer'})
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    booking = models.OneToOneField(Booking, on_delete=models.CASCADE, null=True, blank=True)
    quantity = models.IntegerField(default=1)
    added_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('buyer', 'product')
    
    def __str__(self):
        return f"{self.buyer.user.username} - {self.product.name}"


# =========================================
# CHAT MODEL
# =========================================

class Chat(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='chats')
    buyer = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='buyer_chats')
    seller = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='seller_chats')
    message = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"Chat about {self.product.name} - {self.timestamp}"