from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_POST
from django.template.loader import render_to_string
from django.urls import reverse
from .models import Post, Comment, CustomUser, Conversation, Message, MessageReaction, UserStatus
from django.db.models import Q
import json

@login_required
def home_feed(request):
    # Get posts from users the current user follows
    following_users = request.user.following.all()
    posts = Post.objects.filter(
        Q(author__in=following_users) | Q(author=request.user)
    ).order_by('-created_at')
    
    # Add user initials for posts where profile picture is missing
    for post in posts:
        if not post.author.profile_picture:
            post.author.initials = post.author.username[0].upper()
    
    context = {
        'posts': posts,
        'user': request.user,
    }
    return render(request, 'home.html', context)

@login_required
def explore(request):
    posts = Post.objects.all().order_by('-created_at')
    return render(request, 'explore.html', {'posts': posts})

@login_required
def notifications(request):
    return render(request, 'notifications.html')

@login_required
def messages_view(request, conversation_id=None):
    conversations = request.user.conversations.all().order_by('-updated_at')
    
    # Process each conversation to get proper display info
    for conversation in conversations:
        if not conversation.is_group:
            # For direct messages, get the other participant
            conversation.other_user = conversation.get_other_participant(request.user)
        else:
            # For group chats, use the group name and image
            conversation.display_name = conversation.name or "Group Chat"
            conversation.display_image = conversation.image
        
        # Get last message info - use display_message to avoid conflicting with the property
        conversation.display_message = conversation.messages.order_by('-created_at').first()
        conversation.unread = conversation.messages.exclude(read_by=request.user).exists()
    
    # Get selected conversation if any
    selected_conversation = None
    messages_list = []
    
    if conversation_id:
        selected_conversation = get_object_or_404(Conversation, id=conversation_id, participants=request.user)
        # Get the last 50 messages instead of all messages for better performance
        messages_list = selected_conversation.messages.order_by('-created_at')[:50]
        # Reverse the messages back to chronological order for display
        messages_list = list(reversed(messages_list))
        
        # For direct messages, get the other participant
        if not selected_conversation.is_group:
            selected_conversation.other_user = selected_conversation.get_other_participant(request.user)
        
        # Mark messages as read
        unread_messages = selected_conversation.messages.exclude(read_by=request.user)
        for message in unread_messages:
            message.read_by.add(request.user)
    
    context = {
        'conversations': conversations,
        'selected_conversation': selected_conversation,
        'message_list': messages_list,
    }
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        if request.GET.get('action') == 'get_messages':
            messages_html = render_to_string('includes/messages_list.html', context, request=request)
            return JsonResponse({'messages_html': messages_html})
    
    return render(request, 'messages.html', context)

@login_required
def chat(request, user_id):
    return render(request, 'chat.html')

@login_required
def profile(request, username):
    profile_user = get_object_or_404(CustomUser, username=username)
    posts = Post.objects.filter(author=profile_user).order_by('-created_at')
    is_following = request.user.following.filter(id=profile_user.id).exists()
    
    # Pagination
    paginator = Paginator(posts, 10)
    page = request.GET.get('page', 1)
    
    try:
        posts = paginator.page(page)
    except:
        posts = paginator.page(1)
    
    # If AJAX request, return only the posts HTML
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        posts_html = render_to_string('includes/posts.html', {'posts': posts})
        return HttpResponse(posts_html)
    
    return render(request, 'profile.html', {
        'profile_user': profile_user,
        'posts': posts,
        'is_following': is_following
    })

@login_required
def edit_profile(request, username):
    if request.user.username != username:
        messages.error(request, "You can only edit your own profile.")
        return redirect('core:profile', username=username)
    
    if request.method == 'POST':
        # Handle profile picture upload
        if 'profile_picture' in request.FILES:
            profile_picture = request.FILES['profile_picture']
            if profile_picture.size > 5 * 1024 * 1024:  # 5MB limit
                messages.error(request, "Profile picture must be less than 5MB.")
                return redirect('core:edit_profile', username=username)
            
            # Delete old profile picture if exists
            if request.user.profile_picture:
                request.user.profile_picture.delete()
            
            request.user.profile_picture = profile_picture
        
        # Update user information
        request.user.bio = request.POST.get('bio', '')
        request.user.location = request.POST.get('location', '')
        request.user.website = request.POST.get('website', '')
        request.user.is_private = request.POST.get('is_private') == 'on'
        request.user.show_online_status = request.POST.get('show_online_status') == 'on'
        request.user.email_notifications = request.POST.get('email_notifications') == 'on'
        request.user.push_notifications = request.POST.get('push_notifications') == 'on'
        
        try:
            request.user.save()
            messages.success(request, "Profile updated successfully!")
            return redirect('core:profile', username=username)
        except Exception as e:
            messages.error(request, f"Error updating profile: {str(e)}")
            return redirect('core:edit_profile', username=username)
    
    return render(request, 'edit_profile.html', {'user': request.user})

@login_required
def post_detail(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    comments = post.comments.all().order_by('-created_at')
    
    # Pagination for comments
    paginator = Paginator(comments, 10)
    page = request.GET.get('page', 1)
    
    try:
        comments = paginator.page(page)
    except:
        comments = paginator.page(1)
    
    # If AJAX request, return only the comments HTML
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        comments_html = render_to_string('includes/comments.html', {
            'comments': comments,
            'post': post
        })
        return HttpResponse(comments_html)
    
    return render(request, 'post_detail.html', {
        'post': post,
        'comments': comments
    })

@login_required
def settings(request):
    if request.method == 'POST':
        # Handle general settings updates
        request.user.email_notifications = request.POST.get('email_notifications') == 'on'
        request.user.push_notifications = request.POST.get('push_notifications') == 'on'
        request.user.is_private = request.POST.get('is_private') == 'on'
        request.user.show_online_status = request.POST.get('show_online_status') == 'on'
        request.user.save()
        
        messages.success(request, "Settings updated successfully!")
        return redirect('core:settings')
    
    return render(request, 'settings.html', {
        'user': request.user,
        'dark_mode': request.session.get('dark_mode', False)
    })

@login_required
def profile_settings(request, username):
    if request.user.username != username:
        messages.error(request, "You can only access your own settings.")
        return redirect('core:profile', username=username)
    
    if request.method == 'POST':
        # Handle profile-specific settings
        request.user.is_private = request.POST.get('is_private') == 'on'
        request.user.show_online_status = request.POST.get('show_online_status') == 'on'
        request.user.save()
        messages.success(request, "Profile settings updated successfully!")
        return redirect('core:profile_settings', username=username)
    
    return render(request, 'profile_settings.html', {'user': request.user})

@login_required
def update_profile_picture(request):
    if request.method == 'POST' and 'profile_picture' in request.FILES:
        request.user.profile_picture = request.FILES['profile_picture']
        request.user.save()
        return JsonResponse({'success': True})
    return JsonResponse({'success': False})

@login_required
def create_post(request):
    if request.method == 'POST':
        content = request.POST.get('content')
        image = request.FILES.get('image')
        post = Post.objects.create(author=request.user, content=content, image=image)
        return redirect('core:post_detail', post_id=post.id)
    return render(request, 'create_post.html')

@login_required
def edit_post(request, post_id):
    post = get_object_or_404(Post, id=post_id, author=request.user)
    if request.method == 'POST':
        post.content = request.POST.get('content')
        if 'image' in request.FILES:
            post.image = request.FILES['image']
        post.save()
        return redirect('core:post_detail', post_id=post.id)
    return render(request, 'edit_post.html', {'post': post})

@login_required
@require_POST
def delete_post(request, post_id):
    try:
        post = get_object_or_404(Post, id=post_id, author=request.user)
        post.delete()
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': True})
        messages.success(request, 'Post deleted successfully!')
        return redirect('core:home')
    except Exception as e:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'error': str(e)}, status=400)
        messages.error(request, 'Failed to delete post.')
        return redirect('core:home')

@login_required
def like_post(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    if request.user in post.likes.all():
        post.likes.remove(request.user)
        is_liked = False
    else:
        post.likes.add(request.user)
        is_liked = True
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'is_liked': is_liked,
            'likes_count': post.likes.count()
        })
    return redirect('core:post_detail', post_id=post_id)

@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    if request.method == 'POST':
        content = request.POST.get('content')
        if content:
            comment = Comment.objects.create(post=post, author=request.user, content=content)
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                comment_html = render_to_string('includes/comment.html', {'comment': comment})
                return JsonResponse({
                    'success': True,
                    'html': comment_html,
                    'comments_count': post.comments.count()
                })
            messages.success(request, "Comment added successfully!")
        else:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'error': 'Comment content is required!'
                })
            messages.error(request, "Comment content is required!")
    
    return redirect('core:post_detail', post_id=post_id)

@login_required
def save_post(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    if request.user in post.saved_by.all():
        post.saved_by.remove(request.user)
        is_saved = False
    else:
        post.saved_by.add(request.user)
        is_saved = True
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'is_saved': is_saved,
            'saved_count': post.saved_by.count()
        })
    return redirect('core:post_detail', post_id=post_id)

@login_required
def share_post(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    share_url = request.build_absolute_uri(reverse('core:post_detail', args=[post_id]))
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'share_url': share_url
        })
    return render(request, 'share_post.html', {
        'post': post,
        'share_url': share_url
    })

@login_required
def toggle_theme(request):
    if request.method == 'POST':
        request.session['dark_mode'] = not request.session.get('dark_mode', False)
        return JsonResponse({
            'success': True,
            'dark_mode': request.session['dark_mode']
        })
    return JsonResponse({'success': False})

@login_required
def follow_user(request, username):
    user_to_follow = get_object_or_404(CustomUser, username=username)
    if request.user != user_to_follow:
        request.user.following.add(user_to_follow)
    return JsonResponse({
        'success': True,
        'is_following': True,
        'followers_count': user_to_follow.followers.count()
    })

@login_required
def unfollow_user(request, username):
    user_to_unfollow = get_object_or_404(CustomUser, username=username)
    request.user.following.remove(user_to_unfollow)
    return JsonResponse({
        'success': True,
        'is_following': False,
        'followers_count': user_to_unfollow.followers.count()
    })

@login_required
@require_POST
def send_message(request, conversation_id):
    conversation = get_object_or_404(Conversation, id=conversation_id, participants=request.user)
    
    # Figure out the content source and log it for debugging
    content = None
    content_source = "unknown"
    
    # Check if this is a form submission
    if request.POST.get('content'):
        content = request.POST.get('content')
        content_source = "form"
    else:
        # Try JSON body as a fallback
        try:
            body_unicode = request.body.decode('utf-8')
            data = json.loads(body_unicode)
            content = data.get('content')
            content_source = "json"
        except (json.JSONDecodeError, UnicodeDecodeError) as e:
            # Handle decode error
            return JsonResponse({
                'success': False,
                'error': f'Invalid request format: {str(e)}'
            }, status=400)
    
    # Ensure we have content
    if not content or not content.strip():
        return JsonResponse({
            'success': False,
            'error': 'Message content cannot be empty'
        }, status=400)
    
    # Create the message with the exact content provided
    message = Message.objects.create(
        conversation=conversation,
        sender=request.user,
        content=content,
        message_type='text'
    )
    
    # Handle file uploads
    if 'file' in request.FILES:
        message.file = request.FILES['file']
        message.save()
    
    # Update conversation timestamp
    conversation.save()  # This updates the updated_at field
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or content_source == "json":
        # Return JSON response for AJAX requests
        response_data = {
            'success': True,
            'message': {
                'id': message.id,
                'content': message.content,
                'sender': message.sender.username,
                'sender_id': message.sender.id,
                'is_user': True,  # This message was sent by the current user
                'time': message.created_at.strftime('%I:%M %p'),
                'type': message.message_type,
                'file_url': message.file.url if message.file else None,
                'content_source': content_source,  # Debug info
            }
        }
        return JsonResponse(response_data)
    else:
        # Redirect for regular form submissions
        return redirect('core:messages', conversation_id=conversation.id)

@login_required
@require_POST
def react_to_message(request, message_id):
    message = get_object_or_404(Message, id=message_id)
    data = json.loads(request.body)
    reaction = data.get('reaction')
    
    # Toggle reaction
    existing_reaction = MessageReaction.objects.filter(message=message, user=request.user).first()
    if existing_reaction:
        if existing_reaction.reaction == reaction:
            existing_reaction.delete()
            action = 'removed'
        else:
            existing_reaction.reaction = reaction
            existing_reaction.save()
            action = 'updated'
    else:
        MessageReaction.objects.create(message=message, user=request.user, reaction=reaction)
        action = 'added'
    
    return JsonResponse({
        'success': True,
        'action': action,
        'reaction_count': message.reactions.count()
    })

@login_required
@require_POST
def mark_as_read(request, conversation_id):
    conversation = get_object_or_404(Conversation, id=conversation_id, participants=request.user)
    unread_messages = conversation.messages.exclude(read_by=request.user)
    
    for message in unread_messages:
        message.read_by.add(request.user)
    
    return JsonResponse({'success': True})

@login_required
def update_typing_status(request, conversation_id):
    conversation = get_object_or_404(Conversation, id=conversation_id, participants=request.user)
    is_typing = json.loads(request.body).get('is_typing', False)
    
    user_status, _ = UserStatus.objects.get_or_create(user=request.user)
    user_status.is_typing_in = conversation if is_typing else None
    user_status.save()
    
    return JsonResponse({'success': True})

@login_required
def get_conversation_updates(request, conversation_id):
    conversation = get_object_or_404(Conversation, id=conversation_id, participants=request.user)
    last_message_id = request.GET.get('last_message_id')
    
    # Get new messages (all messages newer than the last one seen)
    if last_message_id:
        new_messages = conversation.messages.filter(id__gt=last_message_id).order_by('created_at')
    else:
        # If no last_message_id, return the last 20 messages
        new_messages = conversation.messages.order_by('-created_at')[:20]
        new_messages = reversed(list(new_messages))
    
    # Get typing status of other participants
    typing_users = UserStatus.objects.filter(
        is_typing_in=conversation
    ).exclude(user=request.user)
    
    response_data = {
        'messages': [{
            'id': msg.id,
            'content': msg.content,
            'sender': msg.sender.username,
            'sender_id': msg.sender.id,
            'is_user': msg.sender.id == request.user.id,
            'time': msg.created_at.strftime('%I:%M %p'),
            'type': msg.message_type,
            'file_url': msg.file.url if msg.file else None,
        } for msg in new_messages],
        'typing_users': [status.user.username for status in typing_users]
    }
    
    return JsonResponse(response_data)

@login_required
def create_conversation(request):
    if request.method == 'POST':
        user_ids = request.POST.getlist('users')
        name = request.POST.get('name')
        is_group = len(user_ids) > 1
        
        if not user_ids:
            messages.error(request, "Please select at least one user to start a conversation.")
            return redirect('core:create_conversation')
        
        # Check if a conversation already exists with the selected user (for direct messages)
        if len(user_ids) == 1:
            existing_conversation = Conversation.objects.filter(
                participants=request.user
            ).filter(
                participants=user_ids[0]
            ).filter(
                is_group=False
            ).first()
            
            if existing_conversation:
                return redirect('core:messages', conversation_id=existing_conversation.id)
        
        # Create new conversation
        conversation = Conversation.objects.create(
            is_group=is_group,
            name=name if is_group else None
        )
        
        # Add participants
        conversation.participants.add(request.user)
        for user_id in user_ids:
            conversation.participants.add(user_id)
        
        # Handle group image if provided
        if is_group and 'image' in request.FILES:
            conversation.image = request.FILES['image']
            conversation.save()
        
        return redirect('core:messages', conversation_id=conversation.id)
    
    # Get users for the create conversation form
    users = CustomUser.objects.exclude(id=request.user.id)
    
    # Prepare user data for the template
    users_data = [{
        'id': user.id,
        'username': user.username,
        'email': user.email,
        'profile_picture': user.profile_picture.url if user.profile_picture else None
    } for user in users]
    
    return render(request, 'create_conversation.html', {
        'users': users_data
    })

@login_required
def search_users(request):
    """API endpoint for searching users to message"""
    query = request.GET.get('q', '').strip()
    
    if len(query) < 2:
        return JsonResponse({'users': []})
    
    users = CustomUser.objects.filter(
        Q(username__icontains=query) | 
        Q(email__icontains=query)
    ).exclude(
        id=request.user.id
    )[:10]  # Limit to 10 results
    
    users_data = [{
        'id': user.id,
        'username': user.username,
        'email': user.email,
        'profile_picture': user.profile_picture.url if user.profile_picture else None
    } for user in users]
    
    return JsonResponse({'users': users_data}) 