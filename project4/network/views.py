from django.contrib.auth import authenticate, login, logout
from django.db import IntegrityError
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.shortcuts import render
from django.urls import reverse
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404

import json

from .models import User, Post, Follow, Like


def index(request):
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


# User post handling
def new_post(request):
    if request.method == "POST":
        content = request.POST["content"]
        user = User.objects.get(pk=request.user.id)
        post = Post(content=content, user=user)
        post.save()
        return HttpResponseRedirect(reverse(index))
    

def edit_post(request, post_id):
    if request.method == "POST":
        data = json.loads(request.body)
        edit_post = Post.objects.get(pk=post_id)
        edit_post.content = data["content"]
        edit_post.save()
        return JsonResponse({"message": "Change successful", "data": data["content"]})


# User profile display handling
def profile(request, user_id):
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

    return render(request, "network/profile.html", {
        "all_posts": all_posts,
        "page_posts": page_posts,
        "username": user.username,
        "followers": followers,
        "following": following,
        "is_following": is_following,
        "profile_user": user
    })


# User like handling
def remove_like(request, post_id):
    try:
        post = Post.objects.get(pk=post_id)
    except Post.DoesNotExist:
        return JsonResponse({"error": "Post not found"}, status=404)
    
    try:
        user = User.objects.get(pk=request.user.id)
    except User.DoesNotExist:
        return JsonResponse({"error": "User not found"}, status=404)
    
    try:
        like = Like.objects.get(user_liking=user, post_liked=post)
        like.delete()
        post.like_count -=1
        post.save()
    except Like.DoesNotExist:
        return JsonResponse({"error": "Like not found"}, status=404)
    
    return JsonResponse({"message": "Like removed successfully"})

def add_like(request, post_id):
    try:
        post = Post.objects.get(pk=post_id)
    except Post.DoesNotExist:
        return JsonResponse({"error": "Post not found"}, status=404)
    
    try:
        user = User.objects.get(pk=request.user.id)
    except User.DoesNotExist:
        return JsonResponse({"error": "User not found"}, status=404)
    
    new_like = Like(user_liking=user, post_liked=post)
    new_like.save()
    post.like_count += 1
    post.save()
    
    return JsonResponse({"message": "Like added successfully"})

# User follow handling
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


def following(request):
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

    return render(request, "network/following.html", {
        "page_posts": page_posts,
    })


# User account handling
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


def logout_view(request):
    logout(request)
    return HttpResponseRedirect(reverse("index"))


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
