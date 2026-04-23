from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db.models import Q
from .models import UserProfile, Category, Product, ProductImage, Cart, Chat
from .forms import SignUpForm, ProductForm, ProductImageForm
from datetime import timedelta
from django.http import JsonResponse

def home(request):
    # Get fresh products (not expired and not booked)
    fresh_products = Product.objects.filter(
        expiry_date__gt=timezone.now(),
        is_available=True,
        booked_by__isnull=True
    ).order_by('-created_at')[:4]
    
    categories = Category.objects.all()
    districts = UserProfile.objects.values_list('district', flat=True).distinct()
    
    context = {
        'fresh_products': fresh_products,
        'categories': categories,
        'districts': districts,
    }
    return render(request, 'app/home.html', context)

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
        product_form = ProductForm(request.POST)
        if product_form.is_valid():
            product = product_form.save(commit=False)
            product.seller = profile
            product.save()
            
            # Handle multiple images
            images = request.FILES.getlist('images')
            for image in images:
                ProductImage.objects.create(product=product, image=image)
            
            messages.success(request, 'Product added successfully!')
            return redirect('seller_dashboard')
    else:
        product_form = ProductForm()
    
    products = Product.objects.filter(seller=profile).order_by('-created_at')
    categories = Category.objects.all()
    
    context = {
        'product_form': product_form,
        'products': products,
        'categories': categories,
    }
    return render(request, 'app/seller_dashboard.html', context)

def all_products(request):
    district = request.GET.get('district', '')
    city = request.GET.get('city', '')
    category = request.GET.get('category', '')
    search = request.GET.get('search', '')
    
    products = Product.objects.filter(
        expiry_date__gt=timezone.now(),
        is_available=True,
        booked_by__isnull=True
    )
    
    if district:
        products = products.filter(district=district)
        cities = UserProfile.objects.filter(district=district).values_list('city', flat=True).distinct()
    else:
        cities = []
    
    if city:
        products = products.filter(city=city)
    
    if category:
        products = products.filter(category__id=category)
    
    if search:
        products = products.filter(Q(name__icontains=search) | Q(description__icontains=search))
    
    categories = Category.objects.all()
    districts = UserProfile.objects.values_list('district', flat=True).distinct()
    
    context = {
        'products': products,
        'categories': categories,
        'districts': districts,
        'cities': cities,
        'selected_district': district,
        'selected_city': city,
        'selected_category': category,
        'search_query': search,
    }
    return render(request, 'app/all_products.html', context)

def product_detail(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    images = product.images.all()
    
    if request.method == 'POST' and request.user.is_authenticated:
        if 'book' in request.POST:
            if request.user.userprofile.user_type == 'buyer':
                product.booked_by = request.user.userprofile
                product.is_available = False
                product.save()
                Cart.objects.create(buyer=request.user.userprofile, product=product)
                messages.success(request, 'Product booked successfully!')
                return redirect('cart')
        
        elif 'message' in request.POST:
            message_text = request.POST.get('message')
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
    }
    return render(request, 'app/product_detail.html', context)

@login_required
def cart_view(request):
    if request.user.userprofile.user_type != 'buyer':
        return redirect('home')
    
    cart_items = Cart.objects.filter(buyer=request.user.userprofile)
    total = sum(item.product.price * item.quantity for item in cart_items)
    
    context = {
        'cart_items': cart_items,
        'total': total,
    }
    return render(request, 'app/cart.html', context)

@login_required
def remove_from_cart(request, cart_id):
    cart_item = get_object_or_404(Cart, id=cart_id, buyer=request.user.userprofile)
    product = cart_item.product
    product.booked_by = None
    product.is_available = True
    product.save()
    cart_item.delete()
    messages.success(request, 'Product removed from cart!')
    return redirect('cart')

def category_products(request, category_id):
    category = get_object_or_404(Category, id=category_id)
    products = Product.objects.filter(
        category=category,
        expiry_date__gt=timezone.now(),
        is_available=True,
        booked_by__isnull=True
    )
    
    context = {
        'category': category,
        'products': products,
    }
    return render(request, 'app/category_products.html', context)


def get_cities(request):
    district = request.GET.get('district')
    if district:
        cities = UserProfile.objects.filter(district=district).values_list('city', flat=True).distinct()
        return JsonResponse({'cities': list(cities)})
    return JsonResponse({'cities': []})