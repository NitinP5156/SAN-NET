from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from .models import Post, Comment
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import timezone

User = get_user_model()

class CoreTests(TestCase):
    def setUp(self):
        # Create test user
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Create another user
        self.other_user = User.objects.create_user(
            username='otheruser',
            email='other@example.com',
            password='testpass123'
        )
        
        # Create test post
        self.post = Post.objects.create(
            author=self.user,
            content='Test post content'
        )
        
        # Create test comment
        self.comment = Comment.objects.create(
            post=self.post,
            author=self.other_user,
            content='Test comment'
        )
        
        # Set up client
        self.client = Client()
        
    def test_home_feed(self):
        # Test home feed for anonymous user
        response = self.client.get(reverse('core:home_feed'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'home_feed.html')
        
        # Test home feed for logged-in user
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('core:home_feed'))
        self.assertEqual(response.status_code, 200)
        
    def test_profile_view(self):
        # Test profile view
        response = self.client.get(reverse('core:profile', kwargs={'username': 'testuser'}))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'profile.html')
        
    def test_post_detail(self):
        # Test post detail view
        response = self.client.get(reverse('core:post_detail', kwargs={'post_id': self.post.id}))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'post_detail.html')
        
    def test_create_post(self):
        # Test post creation
        self.client.login(username='testuser', password='testpass123')
        response = self.client.post(reverse('core:create_post'), {
            'content': 'New test post'
        })
        self.assertEqual(response.status_code, 302)  # Redirect after success
        self.assertTrue(Post.objects.filter(content='New test post').exists())
        
    def test_add_comment(self):
        # Test comment creation
        self.client.login(username='testuser', password='testpass123')
        response = self.client.post(
            reverse('core:add_comment', kwargs={'post_id': self.post.id}),
            {'content': 'New test comment'}
        )
        self.assertEqual(response.status_code, 302)  # Redirect after success
        self.assertTrue(Comment.objects.filter(content='New test comment').exists())
        
    def test_toggle_follow(self):
        # Test follow/unfollow functionality
        self.client.login(username='testuser', password='testpass123')
        response = self.client.post(
            reverse('core:toggle_follow', kwargs={'username': 'otheruser'})
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(self.user.following.filter(username='otheruser').exists())
        
        # Test unfollow
        response = self.client.post(
            reverse('core:toggle_follow', kwargs={'username': 'otheruser'})
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(self.user.following.filter(username='otheruser').exists())
        
    def test_toggle_like(self):
        # Test like/unlike functionality
        self.client.login(username='testuser', password='testpass123')
        response = self.client.post(
            reverse('core:toggle_like', kwargs={'post_id': self.post.id})
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(self.user in self.post.likes.all())
        
        # Test unlike
        response = self.client.post(
            reverse('core:toggle_like', kwargs={'post_id': self.post.id})
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(self.user in self.post.likes.all())
        
    def test_post_with_image(self):
        # Test post creation with image
        self.client.login(username='testuser', password='testpass123')
        image = SimpleUploadedFile(
            "test_image.jpg",
            b"file_content",
            content_type="image/jpeg"
        )
        response = self.client.post(reverse('core:create_post'), {
            'content': 'Post with image',
            'image': image
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Post.objects.filter(content='Post with image').exists())
        
    def test_user_profile_picture(self):
        # Test user profile picture update
        self.client.login(username='testuser', password='testpass123')
        image = SimpleUploadedFile(
            "profile_pic.jpg",
            b"file_content",
            content_type="image/jpeg"
        )
        response = self.client.post(reverse('core:profile', kwargs={'username': 'testuser'}), {
            'profile_picture': image
        })
        self.assertEqual(response.status_code, 200)
        self.assertTrue(User.objects.get(username='testuser').profile_picture) 