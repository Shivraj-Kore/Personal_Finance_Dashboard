from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import UserFile
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import io
import os
from django.conf import settings

from bs4 import BeautifulSoup
import re

def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, 'Login successful!')
            return redirect('home')
        else:
            messages.error(request, 'Invalid username or password')
    return render(request, 'login.html')

def register_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')
        
        if password1 == password2:
            form = UserCreationForm({
                'username': username,
                'password1': password1,
                'password2': password2
            })
            if form.is_valid():
                user = form.save()
                login(request, user)
                messages.success(request, 'Registration successful!')
                return redirect('home')
            else:
                messages.error(request, 'Invalid registration details')
        else:
            messages.error(request, 'Passwords do not match')
    return render(request, 'register.html')

def logout_view(request):
    logout(request)
    return redirect('login')

@login_required(login_url='login')
def home(request):
    if request.method == 'POST':
        uploaded_file = request.FILES.get('fileinput')
        if uploaded_file and uploaded_file.name.endswith('.html'):
            UserFile.objects.create(user=request.user, uploaded_file=uploaded_file)
            return redirect('user_files')
        else:
            return render(request, 'home.html', {'error': 'Only .html files are allowed.'})
    return render(request, 'home.html')

@login_required(login_url='login')
def user_files_view(request):
    user_files = UserFile.objects.filter(user=request.user).order_by('-created_at')
    context = {
        'user_files': user_files,
    }
    return render(request, 'user_files.html', context)


@login_required(login_url='login')
def extract_html_view(request, file_id):
    user_file = get_object_or_404(UserFile, id=file_id, user=request.user)
    
    context = {
        'graph_paths': [],  # Initially, no graph paths
        'file_id': file_id
    }

    return render(request, 'your_report.html', context)


def TotalTransactionsPerMonth(data, year, uname, file_id):
    graph_filename = f'{uname}_transactions_{year}_{file_id}.png'
    graph_filepath = os.path.join(settings.MEDIA_ROOT, 'TSPM', graph_filename)
    
    # Check if the file already exists
    if not os.path.exists(graph_filepath):
        df = pd.DataFrame(data)
        df['day'] = df['day'].astype(int)
        df['amount'] = df['amount'].astype(float)
        # df['transaction'] = df['transaction'].replace('p', 1)
        # df['transaction'] = df['transaction'].replace('r', 0)

        # Filtering the DataFrame
        filtered_df = df[(df['transaction'] == 1) & (df['year'] == year)]

        # Plotting the bar graph
        plt.figure(figsize=(10, 6))
        sns.countplot(data=filtered_df, x='month', order=['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'])
        plt.title(f'Transactions in {year}')
        plt.xlabel('Month')
        plt.ylabel('Number of Transactions')

        # Ensure the directory exists
        graph_dir = os.path.join(settings.MEDIA_ROOT, 'TSPM')
        if not os.path.exists(graph_dir):
            os.makedirs(graph_dir)
        
        # Save the plot as an image file
        plt.savefig(graph_filepath)
        plt.close()
    
    return os.path.join(settings.MEDIA_URL, 'TSPM', graph_filename)

from django.http import JsonResponse

def TotalDebitedPerMonth(data, year, uname, file_id):
    graph_filename = f'{uname}_debited_{year}_{file_id}.png'
    graph_filepath = os.path.join(settings.MEDIA_ROOT, 'TSPM', graph_filename)
    
    # Check if the file already exists
    if not os.path.exists(graph_filepath):
        df = pd.DataFrame(data)
        df['day'] = df['day'].astype(int)
        df['amount'] = df['amount'].astype(float)

        # Filtering the DataFrame
        filtered_df = df[(df['transaction'] == 1) & (df['year'] == year)]

        # Grouping by month and summing the amounts
        monthly_debits = filtered_df.groupby('month')['amount'].sum().reindex(
            ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'], fill_value=0)

        # Plotting the bar graph
        plt.figure(figsize=(10, 6))
        sns.barplot(x=monthly_debits.index, y=monthly_debits.values)
        plt.title(f'Total Debited Amount in {year}')
        plt.xlabel('Month')
        plt.ylabel('Total Amount Debited')

        # Ensure the directory exists
        graph_dir = os.path.join(settings.MEDIA_ROOT, 'TSPM')
        if not os.path.exists(graph_dir):
            os.makedirs(graph_dir)
        
        # Save the plot as an image file
        plt.savefig(graph_filepath)
        plt.close()
    
    return os.path.join(settings.MEDIA_URL, 'TSPM', graph_filename)

@login_required(login_url='login')
def generate_report(request, file_id):
    if request.method == 'POST':
        user_file = get_object_or_404(UserFile, id=file_id, user=request.user)
        
        file_content = user_file.uploaded_file.read()
        
        with io.BytesIO(file_content) as file:
            html = file.read().decode('utf-8')
        
        soup = BeautifulSoup(html, "html.parser")

        sent_paid_data = []
        for outer_cell in soup.find_all(class_="outer-cell"):
            content = outer_cell.find(class_="content-cell").decode_contents().strip()
            content = re.sub(r'\s+', ' ', content)
            if "Sent" in content or "Paid" in content or "Received" in content:
                data = content.split('<br/>')
                sent_paid_data.append(data)
        
        amounts = []
        transactions = []
        months = []
        days = []
        years = []
        rpspat = "₹\d+\.\d+"
        
        for entry in sent_paid_data:
            x = re.search(rpspat, entry[0])
            if x:
                amounts.append(x.group()[1:])
            else:
                amounts.append("0")

            if entry[0].startswith("P") or entry[0].startswith("S"):
                transactions.append(1)
            elif entry[0].startswith("R"):
                transactions.append(0)
            else:
                transactions.append("")

            months.append(entry[1][0:3])
            day_match = re.search(r"\b\d{1,2}\b", entry[1])
            days.append(day_match.group() if day_match else "")
            year_match = re.search(r"\b\d{4}\b", entry[1])
            years.append(year_match.group() if year_match else "")

        data = {
            'amount': amounts,
            'transaction': transactions,
            'month': months,
            'day': days,
            'year': years
        }

        years = sorted(list(set(years)))
        graph_urls = []
        for year in years:
            if year:
                transactions_graph_url = TotalTransactionsPerMonth(data, year, request.user.username, file_id)
                debited_graph_url = TotalDebitedPerMonth(data, year, request.user.username, file_id)
                graph_urls.extend([transactions_graph_url, debited_graph_url])
        
        return JsonResponse({'graph_paths': graph_urls})
    return JsonResponse({'error': 'Invalid request'}, status=400)
