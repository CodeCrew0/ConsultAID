from django.db import models
from django.utils import timezone

class Document(models.Model):
    title = models.CharField(max_length=200)
    file_path = models.CharField(max_length=500)
    content_hash = models.CharField(max_length=64, unique=True)
    uploaded_at = models.DateTimeField(default=timezone.now)
    processed = models.BooleanField(default=False)
    
    def __str__(self):
        return self.title

class ChatLog(models.Model):
    LANGUAGE_CHOICES = [
        ('en', 'English'),
        ('hi', 'Hindi'),
        ('hinglish', 'Hinglish'),
    ]
    
    session_id = models.CharField(max_length=100, db_index=True)
    query = models.TextField()
    response = models.TextField()
    language = models.CharField(max_length=10, choices=LANGUAGE_CHOICES)
    confidence_score = models.FloatField(null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    
    class Meta:
        ordering = ['-created_at']