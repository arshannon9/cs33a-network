from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    pass


class Post(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='author')
    content = models.CharField(max_length=280)
    date = models.DateTimeField(auto_now_add=True)
    like_count = models.IntegerField(default=0)

    def __str__(self):
        return f"Post {self.id} made by {self.user} on {self.date.strftime('%b %d, %Y at %H:%M:%S')}"
    

class Follow(models.Model):
    user_following = models.ForeignKey(User, on_delete=models.CASCADE, related_name="user_following")
    user_followed = models.ForeignKey(User, on_delete=models.CASCADE, related_name="user_followed")

    def __str__(self):
        return f"{self.user_following} is following {self.user_followed}"
    

class Like(models.Model):
    user_liking = models.ForeignKey(User, on_delete=models.CASCADE, related_name="user_liking")
    post_liked = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="post_liked")

    def __str__(self):
        return f"{self.user_liking} liked {self.post_liked}"