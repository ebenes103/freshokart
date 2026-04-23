from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import UserProfile, Product, ProductImage

class SignUpForm(UserCreationForm):
    email = forms.EmailField(required=True)
    phone = forms.CharField(max_length=15)
    address = forms.CharField(widget=forms.Textarea)
    district = forms.CharField(max_length=100)
    city = forms.CharField(max_length=100)
    user_type = forms.ChoiceField(choices=UserProfile.USER_TYPE_CHOICES, widget=forms.RadioSelect)
    
    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2', 'user_type', 'phone', 'address', 'district', 'city')
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
            UserProfile.objects.create(
                user=user,
                user_type=self.cleaned_data['user_type'],
                phone=self.cleaned_data['phone'],
                address=self.cleaned_data['address'],
                district=self.cleaned_data['district'],
                city=self.cleaned_data['city']
            )
        return user

class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['name', 'category', 'description', 'price', 'quantity', 'unit', 'district', 'city']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
        }

class ProductImageForm(forms.ModelForm):
    class Meta:
        model = ProductImage
        fields = ['image']