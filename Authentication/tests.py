# from django.test import TestCase
# from rest_framework.test import APIClient
# from rest_framework import status
# from django.urls import reverse
# from .models import CustomUser
# from rest_framework_simplejwt.tokens import RefreshToken
# class AuthenticationTests(TestCase):
#     def setUp(self):
#         self.client = APIClient()
#         self.user_data = {
#             'username': 'testuser',
#             'email': 'test@example.com',
#             'password': 'testpassword'
#         }
#         self.user = CustomUser.objects.create_user(**self.user_data)
    
#     def test_signup(self):
#         response = self.client.post(reverse('signup'), self.user_data)
#         self.assertEqual(response.status_code, status.HTTP_201_CREATED)
#         self.assertEqual(CustomUser.objects.count(), 2)  # Including the initial user

#     def test_login(self):
#         response = self.client.post(reverse('login'), self.user_data)
#         self.assertEqual(response.status_code, status.HTTP_200_OK)
#         self.assertIn('access', response.data['data'])
    


# class ProfileTests(TestCase):
#     def setUp(self):
#         self.client = APIClient()
#         self.user_data = {
#             'username': 'testuser',
#             'email': 'test@example.com',
#             'password': 'testpassword'
#         }
#         self.user = CustomUser.objects.create_user(**self.user_data)
#         self.client.force_authenticate(user=self.user)
    
#     def test_edit_user_details(self):
#         url = reverse('edit-user-details', kwargs={'id': self.user.id})
#         updated_data = {
#             'full_name': 'Updated Name',
#             'bio': 'Updated bio'
#         }
#         response = self.client.put(url, updated_data, format='json')
#         self.assertEqual(response.status_code, status.HTTP_200_OK)
#         self.assertEqual(response.data['details'], 'Profile updated successfully.')
#         self.assertEqual(response.data['user']['full_name'], updated_data['full_name'])
#         self.assertEqual(response.data['user']['bio'], updated_data['bio'])
    

    
# class LogoutTest(TestCase):
#     def setUp(self):
#         self.client = APIClient()
#         self.user_data = {
#             'username': 'testuser',
#             'email': 'test@example.com',
#             'password': 'testpassword'
#         }
#         self.user = CustomUser.objects.create_user(**self.user_data)
#         self.refresh_token = RefreshToken.for_user(self.user)
    
#     def test_logout(self):
#         url = reverse('logout')
#         data = {'refresh_token': str(self.refresh_token)}
#         response = self.client.post(url, data, format='json')
#         self.assertEqual(response.status_code, status.HTTP_200_OK)
#         # Add more assertions for token invalidation...
    
