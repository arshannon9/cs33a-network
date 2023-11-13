from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import IntegrityError
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.shortcuts import render
from django.urls import reverse
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404

import json

from .models import *


# Index route (default)
def index(request):
    # Logged in users can view all posts
    if request.user.is_authenticated:
        all_posts = Post.objects.all().order_by("id").reverse()

        # Pagination
        paginator = Paginator(all_posts, 10)
        page_number = request.GET.get("page")
        page_posts = paginator.get_page(page_number)

        all_likes = Like.objects.all()

        user_likes = []

        try:
            for like in all_likes:
                if like.user_liking.id == request.user.id:
                    user_likes.append(like.post_liked.id)
        except:
            user_likes = []

        return render(request, "network/index.html", {
            "all_posts": all_posts,
            "page_posts": page_posts,
            "user_likes": user_likes
        })
    # Everyone else is prompted to sign in
    else:
        return HttpResponseRedirect(reverse("login"))


# Create new post
@login_required
def new_post(request):
    if request.method == "POST":
        content = request.POST["content"]
        user = User.objects.get(pk=request.user.id)
        post = Post(content=content, user=user)
        post.save()
        return HttpResponseRedirect(reverse(index))
    
# Edit existing post
@login_required
def edit_post(request, post_id):
    if request.method == "POST":
        data = json.loads(request.body)
        edit_post = Post.objects.get(pk=post_id)
        edit_post.content = data["content"]
        edit_post.save()
        return JsonResponse({"message": "Change successful", "data": data["content"]})


# View user profile and their posts
def profile(request, user_id):
    
    # Logged in users can view user profile
    if request.user.is_authenticated:
        user = get_object_or_404(User, pk=user_id)
        all_posts = Post.objects.filter(user=user).order_by("id").reverse()

        # Followers/Following
        followers = Follow.objects.filter(user_followed=user)
        following = Follow.objects.filter(user_following=user)

        # Check if the current user is following the profile user
        is_following = followers.filter(user_following=request.user).exists()

        # Pagination
        paginator = Paginator(all_posts, 10)
        page_number = request.GET.get("page")
        page_posts = paginator.get_page(page_number)

        all_likes = Like.objects.all()

        user_likes = []

        try:
            for like in all_likes:
                if like.user_liking.id == request.user.id:
                    user_likes.append(like.post_liked.id)
        except:
            user_likes = []

        return render(request, "network/profile.html", {
            "all_posts": all_posts,
            "page_posts": page_posts,
            "username": user.username,
            "followers": followers,
            "following": following,
            "is_following": is_following,
            "profile_user": user,
            "user_likes": user_likes
        })
    # Everyone else is prompted to sign in
    else:
        # Display a message for non-authenticated users
        messages.warning(request, "You must be logged in to view that page.")
        return HttpResponseRedirect(reverse("login"))


# Handle user likes
@login_required
def add_or_remove_like(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    user = get_object_or_404(User, pk=request.user.id)

    try:
        like = Like.objects.get(user_liking=user, post_liked=post)
        like.delete()
        post.like_count -= 1
    except Like.DoesNotExist:
        like = Like(user_liking=user, post_liked=post)
        like.save()
        post.like_count += 1

    post.save()
    return JsonResponse({'like_count': post.like_count})

# Handle user unfollows
@login_required
def unfollow(request):
    user_follow = request.POST["user_follow"]
    user_follow_data = get_object_or_404(User, username=user_follow)
    current_user = User.objects.get(pk=request.user.id)

    try:
        follow = Follow.objects.get(user_following=current_user, user_followed=user_follow_data)
        follow.delete()
    except Follow.DoesNotExist:
        # Handle the case where the Follow object does not exist
        pass

    user_id = user_follow_data.id

    return HttpResponseRedirect(reverse('profile', kwargs={"user_id": user_id}))


# Handle user follows
@login_required
def follow(request):
    user_follow = request.POST["user_follow"]
    user_follow_data = get_object_or_404(User, username=user_follow)
    current_user = User.objects.get(pk=request.user.id)

    try:
        follow = Follow.objects.get(user_following=current_user, user_followed=user_follow_data)
    except Follow.DoesNotExist:
        follow = Follow(user_following=current_user, user_followed=user_follow_data)
        follow.save()

    user_id = user_follow_data.id

    return HttpResponseRedirect(reverse('profile', kwargs={"user_id": user_id}))

# Displays posts from profiles user is following
def following(request):

    # Logged in users can view followed posts
    if request.user.is_authenticated:
        current_user = User.objects.get(pk=request.user.id)
        people_followed = Follow.objects.filter(user_following=current_user)
        all_posts = Post.objects.all().order_by("id").reverse()

        posts_followed = []

        for post in all_posts:
            for person in people_followed:
                if person.user_followed == post.user:
                    posts_followed.append(post)

        # Pagination
        paginator = Paginator(posts_followed, 10)
        page_number = request.GET.get("page")
        page_posts = paginator.get_page(page_number)

        all_likes = Like.objects.all()

        user_likes = []

        try:
            for like in all_likes:
                if like.user_liking.id == request.user.id:
                    user_likes.append(like.post_liked.id)
        except:
            user_likes = []

        return render(request, "network/following.html", {
            "page_posts": page_posts,
            "user_likes": user_likes
        })
    # Everyone else is prompted to sign in
    else:
        # Display a message for non-authenticated users
        messages.warning(request, "You must be logged in to view that page.")
        return HttpResponseRedirect(reverse("login"))


# Log user in
def login_view(request):
    if request.method == "POST":

        # Attempt to sign user in
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)

        # Check if authentication successful
        if user is not None:
            login(request, user)
            return HttpResponseRedirect(reverse("index"))
        else:
            return render(request, "network/login.html", {
                "message": "Invalid username and/or password."
            })
    else:
        return render(request, "network/login.html")


# Log user out
@login_required
def logout_view(request):
    logout(request)
    return HttpResponseRedirect(reverse("index"))

# Register a new user
def register(request):
    if request.method == "POST":
        username = request.POST["username"]
        email = request.POST["email"]

        # Ensure password matches confirmation
        password = request.POST["password"]
        confirmation = request.POST["confirmation"]
        if password != confirmation:
            return render(request, "network/register.html", {
                "message": "Passwords must match."
            })

        # Attempt to create new user
        try:
            user = User.objects.create_user(username, email, password)
            user.save()
        except IntegrityError:
            return render(request, "network/register.html", {
                "message": "Username already taken."
            })
        login(request, user)
        return HttpResponseRedirect(reverse("index"))
    else:
        return render(request, "network/register.html")
