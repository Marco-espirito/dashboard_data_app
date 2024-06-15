from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.db import models
from .models import Sale, Product
from django.contrib import messages
from .forms import UploadFileForm, SaleForm
from .utils import generate_chart
import pandas as pd

def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('home')
    else:
        form = AuthenticationForm()
    return render(request, 'login.html', {'form': form})

@login_required
def home_view(request):
    return render(request, 'home.html')

@login_required
def upload_view(request):
    if request.method == 'POST':
        form = UploadFileForm(request.POST, request.FILES)
        if form.is_valid():
            file = request.FILES['file']
            try:
                data = pd.read_csv(file, sep=";")
                # Vérifiez les colonnes disponibles
                print("Colonnes disponibles :", data.columns)
                # Assurez-vous que les colonnes attendues existent
                required_columns = ['Product', 'Price', 'Quantity', 'Seller', 'Date']
                for col in required_columns:
                    if col not in data.columns:
                        messages.error(request, f"Colonne manquante dans le fichier CSV : {col}")
                        return redirect('upload')
                # Renommer les colonnes si nécessaire
                data.rename(columns={
                    'Product': 'product',
                    'Price': 'price',
                    'Quantity': 'quantity',
                    'Seller': 'seller',
                    'Date': 'date'
                }, inplace=True)
                # Réorganiser les colonnes dans l'ordre souhaité
                data = data[['product', 'price', 'quantity', 'seller', 'date']]
                # Insérer les données dans la base de données
                for _, row in data.iterrows():
                    product_name = row['product']
                    product, _ = Product.objects.get_or_create(name=product_name)
                    Sale.objects.create(
                        product=product,
                        price=row['price'],
                        quantity=row['quantity'],
                        seller=request.user,
                        date=row['date']
                    )
                messages.success(request, "Les données ont été importées avec succès.")
                return redirect('home')
            except Exception as e:
                messages.error(request, f"Erreur lors de l'importation des données : {e}")
                return redirect('upload')
    else:
        form = UploadFileForm()
    return render(request, 'upload.html', {'form': form})

@login_required
def add_sales_view(request):
    if request.method == 'POST':
        form = SaleForm(request.POST)
        if form.is_valid():
            sale = form.save(commit=False)
            sale.seller = request.user
            sale.save()
            return redirect('home')
    else:
        form = SaleForm()
    return render(request, 'add_sales.html', {'form': form})

@login_required
def performance_view(request):
    chart = None
    if request.method == 'POST':
        chart_type = request.POST.get('chart_type')
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')
        
        # Filtrer les données par date si les dates sont fournies
        if start_date and end_date:
            data = Sale.objects.filter(date__range=[start_date, end_date])
        else:
            data = Sale.objects.all()
        
        # Convertir les données en DataFrame
        df = pd.DataFrame(list(data.values('product__name', 'price', 'quantity', 'total_price', 'seller__username', 'date')))
        
        # Vérifiez que la colonne 'date' existe et est de type datetime
        if 'date' in df.columns:
            df['date'] = pd.to_datetime(df['date'])
        else:
            messages.error(request, "La colonne 'date' est manquante dans les données.")
            return redirect('performance')

        # Générer le graphique
        chart = generate_chart(chart_type, df)
    return render(request, 'performance.html', {'chart': chart})

@login_required
def summary_view(request):
    data = Sale.objects.all()
    summary = data.aggregate(total_sales=models.Sum('total_price'))
    return render(request, 'summary.html', {'summary': summary})

def logout_view(request):
    logout(request)
    return redirect('login')
