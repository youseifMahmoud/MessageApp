from django.shortcuts import render, redirect, get_object_or_404 
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.db.models import Q  
from .models import Message, Thread
from .forms import SignUpForm

def home(request):
    return render(request, 'users/home.html')

def signup(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('login')
    else:
        form = SignUpForm()
    return render(request, 'users/signup.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('communicating_with_others')
    else:
        form = AuthenticationForm()
    return render(request, 'users/login.html', {'form': form})

def logout_view(request):
    logout(request)
    return redirect('login')  # Redirect to login page after logout

@login_required
def chat_with_user(request, user_id):
    receiver = get_object_or_404(User, id=user_id)
    thread = Thread.objects.filter(users=request.user).filter(users=receiver).distinct().first()

    if not thread:
        thread = Thread.objects.create()
        thread.users.add(request.user, receiver)

    messages = Message.objects.filter(thread=thread).order_by('timestamp')

    if request.method == 'POST':
        content = request.POST.get('content', '').strip()
        image = request.FILES.get('image')

        if content or image:
            message = Message.objects.create(thread=thread, user=request.user, message=content, image=image)
            # إعادة الرسالة الجديدة كاستجابة AJAX
            return render(request, 'users/message_partial.html', {'message': message})

    # Pass the thread_id to the template to use it in the WebSocket connection
    return render(request, 'users/chat.html', {
        'receiver': receiver,
        'messages': messages,
        'thread': thread,
        'thread_id': thread.id  # تمرير معرف المحادثة إلى القالب
    })

@login_required
def communicating_with_others(request):
    users = User.objects.exclude(id=request.user.id)
    search_query = request.POST.get('search', '')
    if search_query:
        users = users.filter(Q(username__icontains=search_query))

    receiver_id = request.POST.get('receiver_id', '')
    messages = []
    if receiver_id:
        receiver = get_object_or_404(User, id=receiver_id)
        thread = Thread.objects.filter(users=request.user).filter(users=receiver).distinct().first()

        if not thread:
            thread = Thread.objects.create()
            thread.users.add(request.user, receiver)

        messages = Message.objects.filter(thread=thread).order_by('timestamp')

    if request.method == 'POST' and 'content' in request.POST and receiver_id:
        content = request.POST['content'].strip()
        if content:
            Message.objects.create(thread=thread, user=request.user, message=content)
            return redirect('communicating_with_others')

    return render(request, 'users/communicating_with_others.html', {
        'users': users,
        'messages': messages,
        'search_query': search_query,
        'receiver_id': receiver_id
    })
