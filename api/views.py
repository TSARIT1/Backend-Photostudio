# views.py
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.authtoken.models import Token
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.core.mail import send_mail
from django.conf import settings
from .models import *
from .serializers import *
  

class UserRegistrationAPIView(APIView):
    permission_classes = [AllowAny]
    
    def post(self, request):
        serializer = UserRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            token, created = Token.objects.get_or_create(user=user)
            return Response({
                'message': 'User registered successfully',
                'token': token.key,
                'user': UserSerializer(user).data
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class UserLoginAPIView(APIView):
    permission_classes = [AllowAny]
    
    def post(self, request):
        serializer = UserLoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']
            token, created = Token.objects.get_or_create(user=user)
            return Response({
                'message': 'Login successful',
                'token': token.key,
                'user': UserSerializer(user).data
            }, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_401_UNAUTHORIZED)

class PasswordResetRequestAPIView(APIView):
    permission_classes = [AllowAny]
    
    def post(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            try:
                user = User.objects.get(email=email)
                token = default_token_generator.make_token(user)
                uid = urlsafe_base64_encode(force_bytes(user.pk))
                
                # Create reset link
                reset_link = f"http://localhost:3000/reset-password/{uid}/{token}/"
                
                # Send email
                subject = "Password Reset Request"
                message = f"Hello {user.username},\n\nPlease click the link below to reset your password:\n\n{reset_link}\n\nIf you didn't request this, please ignore this email."
                send_mail(
                    subject, 
                    message, 
                    settings.EMAIL_HOST_USER, 
                    [user.email], 
                    fail_silently=False
                )
                
                return Response({
                    'message': 'Password reset link has been sent to your email.'
                }, status=status.HTTP_200_OK)
            except User.DoesNotExist:
                # Don't reveal that the user doesn't exist
                return Response({
                    'message': 'If that email exists in our system, we have sent a password reset link.'
                }, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class PasswordResetConfirmAPIView(APIView):
    permission_classes = [AllowAny]
    
    def post(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        if serializer.is_valid():
            token = serializer.validated_data['token']
            password = serializer.validated_data['password']
            
            try:
                uid = force_str(urlsafe_base64_decode(request.data.get('uid')))
                user = User.objects.get(pk=uid)
                
                if default_token_generator.check_token(user, token):
                    user.set_password(password)
                    user.save()
                    return Response({
                        'message': 'Password has been reset successfully.'
                    }, status=status.HTTP_200_OK)
                else:
                    return Response({
                        'error': 'Invalid or expired token.'
                    }, status=status.HTTP_400_BAD_REQUEST)
            except (TypeError, ValueError, OverflowError, User.DoesNotExist):
                return Response({
                    'error': 'Invalid token or user.'
                }, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

from rest_framework import viewsets, mixins


class UserViewSet(mixins.RetrieveModelMixin,
                  mixins.UpdateModelMixin,
                  viewsets.GenericViewSet):
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        # Always return the authenticated user
        return self.request.user


from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models.functions import ExtractWeekDay
from django.db.models import Count
import calendar

class CrmViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = CrmSerializer

    def get_queryset(self):
        return Crm.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=False, methods=["get"])
    def status_by_day(self, request):
        queryset = self.get_queryset()
        
        # Extract day of week and group by status
        data = queryset.annotate(
            weekday=ExtractWeekDay("created_at")  # 1=Sunday, 2=Monday, ..., 7=Saturday
        ).values("weekday", "status").annotate(
            count=Count("id")
        )

        # Define fixed days and statuses
        days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        statuses = ["New", "Follow-up", "Closed"]

        # Initialize result with zeros
        result = {day: {status: 0 for status in statuses} for day in days}

        # Fill in actual counts
        for entry in data:
            weekday_index = (entry["weekday"] - 2) % 7  # Shift: 1=Sunday -> index 6, 2=Monday -> index 0
            day_name = days[weekday_index]
            status = entry["status"]
            if status in statuses:
                result[day_name][status] = entry["count"]

        return Response(result)
       
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from .models import Invoice, ServiceItem
from .serializers import InvoiceSerializer
from django.db.models import Q
from django.db.models import Sum

class InvoiceViewSet(viewsets.ModelViewSet):
    serializer_class = InvoiceSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        return Invoice.objects.filter(created_by=user)
    
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
    
    @action(detail=True, methods=['post'])
    def mark_as_paid(self, request, pk=None):
        invoice = self.get_object()
        invoice.status = 'paid'
        invoice.save()
        return Response({'status': 'invoice marked as paid'})
    
    @action(detail=True, methods=['post'])
    def mark_as_sent(self, request, pk=None):
        invoice = self.get_object()
        invoice.status = 'sent'
        invoice.save()
        return Response({'status': 'invoice marked as sent'})
    
    @action(detail=False, methods=['get'])
    def search(self, request):
        query = request.query_params.get('q', '')
        invoices = self.get_queryset().filter(
            Q(invoice_number__icontains=query) |
            Q(customer_name__icontains=query) |
            Q(customer_address__icontains=query)
        )
        serializer = self.get_serializer(invoices, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        user = request.user
        total_invoices = Invoice.objects.filter(created_by=user).count()
        total_revenue = Invoice.objects.filter(
            created_by=user, 
            status='paid'
        ).aggregate(Sum('total_amount'))['total_amount__sum'] or 0
        
        return Response({
            'total_invoices': total_invoices,
            'total_revenue': float(total_revenue),
            'pending_invoices': Invoice.objects.filter(
                created_by=user, 
                status__in=['draft', 'sent']
            ).count()
        })
    




from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from .models import DataStore
from .serializers import DataStoreSerializer
from django.contrib.auth import get_user_model

User = get_user_model()

class DataStoreViewSet(viewsets.ModelViewSet):
    serializer_class = DataStoreSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        # Return only files belonging to the authenticated user
        return DataStore.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        # Automatically set the user to the current authenticated user
        serializer.save(user=self.request.user)
    
    def create(self, request, *args, **kwargs):
        # Handle file upload
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
    
    @action(detail=False, methods=['get'])
    def photos(self, request):
        photos = self.get_queryset().filter(file_type='photo')
        serializer = self.get_serializer(photos, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def videos(self, request):
        videos = self.get_queryset().filter(file_type='video')
        serializer = self.get_serializer(videos, many=True)
        return Response(serializer.data)
    
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        
        # Check if the user owns this file
        if instance.user != request.user:
            return Response(
                {"error": "You don't have permission to delete this file."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Delete the actual file from storage
        instance.file.delete()
        
        # Delete the database record
        self.perform_destroy(instance)
        
        return Response(status=status.HTTP_204_NO_CONTENT)