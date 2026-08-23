import re
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Listing

class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True

class MultipleFileField(forms.ImageField):
    widget = MultipleFileInput

    def clean(self, data, initial=None):
        single_file_clean = super().clean
        if isinstance(data, (list, tuple)):
            return [single_file_clean(d, initial) for d in data]
        return [single_file_clean(data, initial)]

class ListingForm(forms.ModelForm):
    image = MultipleFileField(
        widget=MultipleFileInput(attrs={'class': 'form-control', 'multiple': True}),
        label='Фотографии лота (первая станет обложкой)',
        required=False
    )

    class Meta:
        model = Listing
        # Добавляем article в список полей
        fields = ('title', 'article', 'description', 'starting_bid', 'category')
        
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Например, Darth Vader'}),
            'article': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Например: sw0004, sh0123, njo0045'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Подробное описание', 'rows': 4}),
            'starting_bid': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'От 100 до 300'}),
            'category': forms.Select(attrs={'class': 'form-control'}),
        }
        
        labels = {
            'title': 'Название лота',
            'article': 'Артикул фигурки (например, sw0004)',
            'description': 'Описание',
            'starting_bid': 'Начальная цена (₽)',
            'category': 'Категория',
        }

    def clean(self):
        cleaned_data = super().clean()
        article = cleaned_data.get('article')
        category = cleaned_data.get('category')

        if not article or not category:
            return cleaned_data

        cat_name = category.name.lower()
        article = article.strip().lower()

        # Проверка для Star Wars (sw + 4 цифры)
        if 'star wars' in cat_name:
            if not re.match(r'^sw\d{4}$', article):
                raise forms.ValidationError("Для категории Star Wars артикул должен начинаться с 'sw' и содержать ровно 4 цифры (например: sw0004).")
        
        # Проверка для Super Heroes (sh + 4 цифры)
        elif 'super heroes' in cat_name:
            if not re.match(r'^sh\d{4}$', article):
                raise forms.ValidationError("Для категории Super Heroes артикул должен начинаться с 'sh' и содержать ровно 4 цифры (например: sh0123).")
        
        # Проверка для Ninjago (njo + 4 цифры)
        elif 'ninjago' in cat_name:
            if not re.match(r'^njo\d{4}$', article):
                raise forms.ValidationError("Для категории Ninjago артикул должен начинаться с 'njo' и содержать ровно 4 цифры (например: njo0045).")

        return cleaned_data

    def clean_title(self):
        title = self.cleaned_data.get('title')
        if re.search('[а-яА-ЯёЁ]', title):
            raise forms.ValidationError("Название лота должно быть написано только на латинице (английскими буквами).")
        return title

class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ('username', 'email')
        
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Придумайте имя'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Ваш email'}),
        }
        
        labels = {
            'username': 'Имя пользователя',
            'email': 'Email адрес',
        }