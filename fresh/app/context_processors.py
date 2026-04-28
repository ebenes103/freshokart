from .models import Cart

def cart_count(request):
    if request.user.is_authenticated and hasattr(request.user, 'userprofile'):
        if request.user.userprofile.user_type == 'buyer':
            count = Cart.objects.filter(
                buyer=request.user.userprofile,
                booking__status='active'
            ).count()
            return {'cart_count': count}
    return {'cart_count': 0}