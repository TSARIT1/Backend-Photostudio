# serializers.py
from rest_framework import serializers
from django.contrib.auth import authenticate
from .models import *

class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    confirm_password = serializers.CharField(write_only=True, min_length=8)
    
    class Meta:
        model = User
        fields = ('id', 'email', 'username', 'password', 'confirm_password', 'first_name', 'last_name')
    
    def validate(self, data):
        if data['password'] != data['confirm_password']:
            raise serializers.ValidationError("Passwords do not match.")
        return data
    
    def create(self, validated_data):
        validated_data.pop('confirm_password')
        user = User.objects.create_user(**validated_data)
        return user

class UserLoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField()
    
    def validate(self, data):
        email = data.get('email')
        password = data.get('password')
        
        if email and password:
            user = authenticate(username=email, password=password)
            if user:
                if user.is_active:
                    data['user'] = user
                else:
                    raise serializers.ValidationError("User account is disabled.")
            else:
                raise serializers.ValidationError("Invalid credentials.")
        else:
            raise serializers.ValidationError("Must provide email and password.")
        return data

class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()

class PasswordResetConfirmSerializer(serializers.Serializer):
    password = serializers.CharField(min_length=8)
    confirm_password = serializers.CharField(min_length=8)
    token = serializers.CharField()
    
    def validate(self, data):
        if data['password'] != data['confirm_password']:
            raise serializers.ValidationError("Passwords do not match.")
        return data

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'email', 'username', 'first_name', 'last_name', 'created_at', 'updated_at',"phone_number","profile_photo","location","role")

class CrmSerializer(serializers.ModelSerializer):
    class Meta:
        model = Crm
        fields = "__all__"
        read_only_fields = ["user"]        



class ServiceItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = ServiceItem
        fields = ['id', 'name', 'cost', 'quantity', 'total']
        read_only_fields = ['total']

class InvoiceSerializer(serializers.ModelSerializer):
    services = ServiceItemSerializer(many=True)
    
    class Meta:
        model = Invoice
        fields = [
            'id', 'invoice_number', 'date', 'customer_name', 
            'customer_address', 'tax_number', 'prepared_by',
            'services', 'subtotal', 'tax_rate', 'tax_amount', 
            'total_amount', 'status', 'created_by', 'created_at',
            'updated_at'
        ]
        read_only_fields = ['id', 'created_by', 'created_at', 'updated_at']

    def create(self, validated_data):
        services_data = validated_data.pop('services')
        invoice = Invoice.objects.create(**validated_data)
        
        for service_data in services_data:
            ServiceItem.objects.create(invoice=invoice, **service_data)
        
        return invoice

    def update(self, instance, validated_data):
        services_data = validated_data.pop('services', None)
        
        # Update invoice fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        # Update services if provided
        if services_data is not None:
            # Delete existing services
            instance.services.all().delete()
            
            # Create new services
            for service_data in services_data:
                ServiceItem.objects.create(invoice=instance, **service_data)
        
        return instance
    



class DataStoreSerializer(serializers.ModelSerializer):
    class Meta:
        model = DataStore
        fields = ['id', 'name', 'file', 'file_type', 'file_format', 'size', 'uploaded_at']
        read_only_fields = ['id', 'file_type', 'file_format', 'size', 'uploaded_at']
    
    def create(self, validated_data):
        # Set the user from the request
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)