from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError

def validate_html_file(value):
    if not value.name.endswith('.html'):
        raise ValidationError('Only .html files are allowed.')

class UserFile(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    uploaded_file = models.FileField(upload_to='userFiles/', validators=[validate_html_file])
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.uploaded_file.name}"


class GeneratedGraph(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    graph_file = models.ImageField(upload_to='generated_graphs/')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.graph_file.name}"
