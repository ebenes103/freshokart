from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db.models import Q
from django.http import JsonResponse
from datetime import timedelta
from .models import UserProfile, Category, Product, ProductImage, Cart, Chat, Booking, District, City
from .forms import SignUpForm, ProductForm, ProductImageForm
from django.db import models

def home(request):
    # Get fresh products for featured section (within 3 days, not fully booked)
    fresh_products = Product.objects.filter(
        created_at__gte=timezone.now() - timedelta(days=3)
    ).order_by('-created_at')[:4]
    
    # Calculate available quantity for each product
    for product in fresh_products:
        product.available_qty = product.quantity_left()
    
    categories = Category.objects.all()
    districts = District.objects.all()
    
    context = {
        'fresh_products': fresh_products,
        'categories': categories,
        'districts': districts,
    }
    return render(request, 'app/home.html', context)

@login_required
def book_product(request, product_id):
    """Book a product"""
    product = get_object_or_404(Product, id=product_id)
    
    if request.user.userprofile.user_type != 'buyer':
        messages.error(request, 'Only buyers can book products')
        return redirect('product_detail', product_id=product_id)
    
    # Check if product has available quantity
    if product.quantity_left() <= 0:
        messages.error(request, 'Sorry, this product is out of stock!')
        return redirect('product_detail', product_id=product_id)
    
    # Check if user already has an active booking for this product
    existing_booking = Booking.objects.filter(
        product=product,
        buyer=request.user.userprofile,
        status='active'
    ).first()
    
    if existing_booking:
        messages.warning(request, 'You have already booked this product!')
        return redirect('cart')
    
    # Create booking
    booking = Booking.objects.create(
        product=product,
        buyer=request.user.userprofile,
        quantity=1,
        total_price=product.price,
        status='active'
    )
    
    # Update product quantities
    product.quantity_booked += 1
    product.save()
    
    # Add to cart
    cart_item, created = Cart.objects.get_or_create(
        buyer=request.user.userprofile,
        product=product,
        defaults={'booking': booking, 'quantity': 1}
    )
    if not created:
        cart_item.booking = booking
        cart_item.save()
    
    messages.success(request, f'{product.name} has been booked and added to your cart!')
    return redirect('cart')

@login_required
def cancel_booking(request, booking_id):
    """Cancel a booking"""
    booking = get_object_or_404(Booking, id=booking_id, buyer=request.user.userprofile)
    
    if booking.status == 'active':
        booking.status = 'cancelled'
        booking.cancelled_at = timezone.now()
        booking.save()
        
        # Release the product quantity
        product = booking.product
        product.quantity_booked = max(0, product.quantity_booked - booking.quantity)
        product.save()
        
        # Remove from cart
        Cart.objects.filter(booking=booking).delete()
        
        messages.success(request, f'Booking for {product.name} has been cancelled.')
    else:
        messages.error(request, 'This booking cannot be cancelled')
    
    return redirect('cart')

@login_required
def cart_view(request):
    if request.user.userprofile.user_type != 'buyer':
        messages.error(request, 'Only buyers can view cart')
        return redirect('home')
    
    # Get all active bookings for this buyer
    cart_items = Cart.objects.filter(
        buyer=request.user.userprofile,
        booking__status='active'
    ).select_related('product', 'booking')
    
    # Calculate total
    total = sum(item.product.price * item.quantity for item in cart_items)
    
    # Get booking details for each item
    for item in cart_items:
        item.booking_expires = item.booking.expires_at if item.booking else None
        item.remaining_time = item.booking.expires_at - timezone.now() if item.booking else None
    
    context = {
        'cart_items': cart_items,
        'total': total,
    }
    return render(request, 'app/cart.html', context)

@login_required
def get_cart_count(request):
    if request.user.is_authenticated and hasattr(request.user, 'userprofile'):
        if request.user.userprofile.user_type == 'buyer':
            count = Cart.objects.filter(
                buyer=request.user.userprofile,
                booking__status='active'
            ).count()
            return JsonResponse({'count': count})
    return JsonResponse({'count': 0})

@login_required
def remove_from_cart(request, cart_id):
    """Remove item from cart (same as cancel booking)"""
    cart_item = get_object_or_404(Cart, id=cart_id, buyer=request.user.userprofile)
    
    if cart_item.booking:
        return cancel_booking(request, cart_item.booking.id)
    else:
        cart_item.delete()
        messages.success(request, 'Item removed from cart')
    
    return redirect('cart')

def signup(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            if form.cleaned_data['user_type'] == 'seller':
                return redirect('seller_dashboard')
            else:
                return redirect('home')
    else:
        form = SignUpForm()
    return render(request, 'app/signup.html', {'form': form})

def user_login(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            profile = UserProfile.objects.get(user=user)
            if profile.user_type == 'seller':
                return redirect('seller_dashboard')
            else:
                return redirect('home')
        else:
            messages.error(request, 'Invalid username or password')
    return render(request, 'app/login.html')

def user_logout(request):
    logout(request)
    return redirect('home')

@login_required
def seller_dashboard(request):
    profile = request.user.userprofile
    if profile.user_type != 'seller':
        return redirect('home')
    
    if request.method == 'POST':
        # Get form data manually
        name = request.POST.get('name')
        category_id = request.POST.get('category')
        description = request.POST.get('description')
        price = request.POST.get('price')
        unit = request.POST.get('unit')
        quantity_available = request.POST.get('quantity_available')
        district_id = request.POST.get('district')
        city_id = request.POST.get('city')
        
        # Create product
        product = Product.objects.create(
            seller=profile,
            category_id=category_id,
            name=name,
            description=description,
            price=price,
            unit=unit,
            quantity_available=quantity_available,
            quantity_booked=0,
            district_id=district_id,
            city_id=city_id
        )
        
        # Handle images
        images = request.FILES.getlist('images')
        for image in images:
            ProductImage.objects.create(product=product, image=image)
        
        messages.success(request, 'Product added successfully!')
        return redirect('seller_dashboard')
    
    products = Product.objects.filter(seller=profile).order_by('-created_at')
    
    # Calculate statistics for each product
    for product in products:
        product.available_qty = product.quantity_left()
        product.active_bookings = product.bookings.filter(status='active').count()
    
    categories = Category.objects.all()
    districts = District.objects.all()
    
    context = {
        'products': products,
        'categories': categories,
        'districts': districts,
    }
    return render(request, 'app/seller_dashboard.html', context)

def all_products(request):
    # Get filter parameters
    district_id = request.GET.get('district')
    city_id = request.GET.get('city')
    category_name = request.GET.get('category')
    search_query = request.GET.get('search', '')
    
    # Start with products that are fresh and have available stock
    products = Product.objects.filter(
        created_at__gte=timezone.now() - timedelta(days=5)
    ).exclude(
        quantity_available=models.F('quantity_booked')
    )
    
    # Apply district filter
    selected_district = None
    if district_id:
        try:
            selected_district = District.objects.get(id=district_id)
            products = products.filter(district=selected_district)
        except District.DoesNotExist:
            pass
    
    # Apply city filter
    selected_city = None
    if city_id:
        try:
            selected_city = City.objects.get(id=city_id)
            products = products.filter(city=selected_city)
        except City.DoesNotExist:
            pass
    
    # Apply category filter
    if category_name and category_name != '':
        products = products.filter(category__name__iexact=category_name)
    
    # Apply search filter
    if search_query:
        products = products.filter(
            Q(name__icontains=search_query) |
            Q(description__icontains=search_query)
        )
    
    # Get all categories, districts, and cities for filters
    categories = Category.objects.all()
    districts = District.objects.all()
    
    # Get cities for selected district
    cities = []
    if selected_district:
        cities = City.objects.filter(district=selected_district)
    
    context = {
        'products': products,
        'categories': categories,
        'districts': districts,
        'cities': cities,
        'selected_district': district_id,
        'selected_city': city_id,
        'selected_category': category_name,
        'search_query': search_query,
    }
    return render(request, 'app/all_products.html', context)

def category_products(request, category_id):
    """View for products in a specific category with district/city filters"""
    category = get_object_or_404(Category, id=category_id)
    
    # Get filter parameters
    district_id = request.GET.get('district')
    city_id = request.GET.get('city')
    search_query = request.GET.get('search', '')
    
    # Start with products in this category that are fresh and have available stock
    products = Product.objects.filter(
        category=category,
        created_at__gte=timezone.now() - timedelta(days=5)
    ).exclude(
        quantity_available=models.F('quantity_booked')
    )
    
    # Apply district filter
    selected_district = None
    if district_id:
        try:
            selected_district = District.objects.get(id=district_id)
            products = products.filter(district=selected_district)
        except District.DoesNotExist:
            pass
    
    # Apply city filter
    selected_city = None
    if city_id:
        try:
            selected_city = City.objects.get(id=city_id)
            products = products.filter(city=selected_city)
        except City.DoesNotExist:
            pass
    
    # Apply search filter
    if search_query:
        products = products.filter(
            Q(name__icontains=search_query) |
            Q(description__icontains=search_query)
        )
    
    # Get all categories, districts, and cities for filters
    categories = Category.objects.all()
    districts = District.objects.all()
    
    # Get cities for selected district
    cities = []
    if selected_district:
        cities = City.objects.filter(district=selected_district)
    
    context = {
        'category': category,
        'products': products,
        'categories': categories,
        'districts': districts,
        'cities': cities,
        'selected_district': district_id,
        'selected_city': city_id,
        'search_query': search_query,
    }
    return render(request, 'app/category_products.html', context)

def product_detail(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    images = product.images.all()
    
    # Get related products (same category, excluding current)
    related_products = Product.objects.filter(
        category=product.category
    ).exclude(id=product.id)[:4]
    
    if request.method == 'POST' and request.user.is_authenticated:
        if 'message' in request.POST:
            message_text = request.POST.get('message')
            if message_text:
                Chat.objects.create(
                    product=product,
                    buyer=request.user.userprofile,
                    seller=product.seller,
                    message=message_text
                )
                messages.success(request, 'Message sent to seller!')
    
    context = {
        'product': product,
        'images': images,
        'related_products': related_products,
    }
    return render(request, 'app/product_detail.html', context)

@login_required
def cart_view(request):
    if request.user.userprofile.user_type != 'buyer':
        return redirect('home')
    
    cart_items = Cart.objects.filter(
        buyer=request.user.userprofile,
        booking__status='active'
    )
    
    total = sum(item.product.price * item.quantity for item in cart_items)
    
    context = {
        'cart_items': cart_items,
        'total': total,
    }
    return render(request, 'app/cart.html', context)

def get_districts(request):
    """API endpoint to get all districts"""
    districts = District.objects.all().values('id', 'name')
    return JsonResponse({'districts': list(districts)})

def get_cities(request):
    """API endpoint to get cities for a specific district"""
    district_id = request.GET.get('district_id')
    if district_id:
        cities = City.objects.filter(district_id=district_id).values('id', 'name')
        return JsonResponse({'cities': list(cities)})
    return JsonResponse({'cities': []})

@login_required
def send_message(request, product_id):
    """Send a message to seller"""
    if request.method == 'POST':
        product = get_object_or_404(Product, id=product_id)
        message_text = request.POST.get('message')
        
        if message_text and request.user.userprofile.user_type == 'buyer':
            Chat.objects.create(
                product=product,
                buyer=request.user.userprofile,
                seller=product.seller,
                message=message_text
            )
            messages.success(request, 'Message sent to seller!')
        else:
            messages.error(request, 'Failed to send message')
    
    return redirect('product_detail', product_id=product_id)