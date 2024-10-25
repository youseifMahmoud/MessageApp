from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class Thread(models.Model):
    users = models.ManyToManyField(User)  
    updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Thread between {', '.join([user.username for user in self.users.all()])}"

class Message(models.Model):
    thread = models.ForeignKey(Thread, related_name='messages', on_delete=models.CASCADE, null=True, blank=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    message = models.TextField(blank=True)  # Make message optional for image-only messages
    image = models.ImageField(upload_to='chat_images/', blank=True, null=True)  # Field to store images
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Message from {self.user.username}"
