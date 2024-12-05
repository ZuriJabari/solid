# Authentication Implementation

## Backend Implementation

### 1. Custom User Manager (accounts/managers.py)
```python
from django.contrib.auth.base_user import BaseUserManager
from django.utils.translation import gettext_lazy as _

class CustomUserManager(BaseUserManager):
    def create_user(self, email, password, **extra_fields):
        if not email:
            raise ValueError(_('Email is required'))
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save()
        return user

    def create_superuser(self, email, password, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        extra_fields.setdefault('verified', True)
        return self.create_user(email, password, **extra_fields)
```

### 2. Serializers (accounts/serializers.py)
```python
from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.core.validators import RegexValidator
from datetime import date

User = get_user_model()

class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    confirm_password = serializers.CharField(write_only=True)
    phone = serializers.CharField(
        validators=[RegexValidator(r'^\+[1-9]\d{1,14}$')]
    )
    date_of_birth = serializers.DateField()

    class Meta:
        model = User
        fields = ('email', 'phone', 'password', 'confirm_password', 
                 'date_of_birth', 'first_name', 'last_name')

    def validate_date_of_birth(self, value):
        today = date.today()
        age = today.year - value.year - ((today.month, today.day) < 
                                       (value.month, value.day))
        if age < 18:
            raise serializers.ValidationError("Must be at least 18 years old")
        return value

    def validate(self, data):
        if data['password'] != data.pop('confirm_password'):
            raise serializers.ValidationError("Passwords do not match")
        return data

class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField()

class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'email', 'phone', 'first_name', 'last_name', 
                 'date_of_birth', 'address', 'verified')
        read_only_fields = ('email', 'verified')
```

### 3. Views (accounts/views.py)
```python
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from .serializers import (UserRegistrationSerializer, LoginSerializer, 
                         UserProfileSerializer)

class RegisterView(generics.CreateAPIView):
    permission_classes = (AllowAny,)
    serializer_class = UserRegistrationSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        refresh = RefreshToken.for_user(user)
        
        return Response({
            'user': UserProfileSerializer(user).data,
            'tokens': {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            }
        }, status=status.HTTP_201_CREATED)

class LoginView(generics.GenericAPIView):
    permission_classes = (AllowAny,)
    serializer_class = LoginSerializer

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = authenticate(
            email=serializer.validated_data['email'],
            password=serializer.validated_data['password']
        )
        if not user:
            return Response(
                {'error': 'Invalid credentials'}, 
                status=status.HTTP_401_UNAUTHORIZED
            )
            
        refresh = RefreshToken.for_user(user)
        return Response({
            'user': UserProfileSerializer(user).data,
            'tokens': {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            }
        })

class ProfileView(generics.RetrieveUpdateAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = UserProfileSerializer

    def get_object(self):
        return self.request.user
```

## Frontend Implementation (Web)

### 1. Redux Store Setup (src/store/authSlice.ts)
```typescript
import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import axios from 'axios';

interface AuthState {
  user: any | null;
  tokens: {
    access: string | null;
    refresh: string | null;
  };
  loading: boolean;
  error: string | null;
}

const initialState: AuthState = {
  user: null,
  tokens: {
    access: localStorage.getItem('accessToken'),
    refresh: localStorage.getItem('refreshToken'),
  },
  loading: false,
  error: null,
};

export const register = createAsyncThunk(
  'auth/register',
  async (userData: any) => {
    const response = await axios.post('/api/auth/register/', userData);
    return response.data;
  }
);

export const login = createAsyncThunk(
  'auth/login',
  async (credentials: { email: string; password: string }) => {
    const response = await axios.post('/api/auth/login/', credentials);
    return response.data;
  }
);

const authSlice = createSlice({
  name: 'auth',
  initialState,
  reducers: {
    logout: (state) => {
      state.user = null;
      state.tokens.access = null;
      state.tokens.refresh = null;
      localStorage.removeItem('accessToken');
      localStorage.removeItem('refreshToken');
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(register.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(register.fulfilled, (state, action) => {
        state.loading = false;
        state.user = action.payload.user;
        state.tokens = action.payload.tokens;
        localStorage.setItem('accessToken', action.payload.tokens.access);
        localStorage.setItem('refreshToken', action.payload.tokens.refresh);
      })
      .addCase(register.rejected, (state, action) => {
        state.loading = false;
        state.error = action.error.message || 'Registration failed';
      })
      // Similar cases for login...
  },
});

export const { logout } = authSlice.actions;
export default authSlice.reducer;
```

### 2. Authentication Components (src/components/auth)

```typescript
// RegisterForm.tsx
import React from 'react';
import { useFormik } from 'formik';
import * as Yup from 'yup';
import { useAppDispatch } from '../../store/hooks';
import { register } from '../../store/authSlice';

const RegisterForm = () => {
  const dispatch = useAppDispatch();

  const formik = useFormik({
    initialValues: {
      email: '',
      password: '',
      confirmPassword: '',
      phone: '',
      dateOfBirth: '',
      firstName: '',
      lastName: '',
    },
    validationSchema: Yup.object({
      email: Yup.string()
        .email('Invalid email address')
        .required('Required'),
      password: Yup.string()
        .min(8, 'Must be at least 8 characters')
        .required('Required'),
      confirmPassword: Yup.string()
        .oneOf([Yup.ref('password')], 'Passwords must match')
        .required('Required'),
      phone: Yup.string()
        .matches(/^\+[1-9]\d{1,14}$/, 'Invalid phone number')
        .required('Required'),
      dateOfBirth: Yup.date()
        .max(new Date(Date.now() - 567648000000), 'Must be at least 18')
        .required('Required'),
      firstName: Yup.string().required('Required'),
      lastName: Yup.string().required('Required'),
    }),
    onSubmit: (values) => {
      dispatch(register(values));
    },
  });

  return (
    <form onSubmit={formik.handleSubmit} className="space-y-6">
      <div>
        <label className="block text-sm font-medium text-gray-700">
          Email
        </label>
        <input
          type="email"
          {...formik.getFieldProps('email')}
          className="mt-1 block w-full rounded-md border-gray-300 shadow-sm"
        />
        {formik.touched.email && formik.errors.email && (
          <div className="text-red-500 text-sm">{formik.errors.email}</div>
        )}
      </div>
      {/* Similar fields for other inputs */}
      <button
        type="submit"
        className="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700"
      >
        Register
      </button>
    </form>
  );
};

export default RegisterForm;
```

## Mobile Implementation (React Native)

### 1. Authentication Screens

```typescript
// screens/auth/RegisterScreen.tsx
import React from 'react';
import { View, ScrollView } from 'react-native';
import { TextInput, Button, HelperText } from 'react-native-paper';
import { useFormik } from 'formik';
import * as Yup from 'yup';
import { useAppDispatch } from '../../store/hooks';
import { register } from '../../store/authSlice';

const RegisterScreen = () => {
  const dispatch = useAppDispatch();

  const formik = useFormik({
    initialValues: {
      email: '',
      password: '',
      confirmPassword: '',
      phone: '',
      dateOfBirth: '',
      firstName: '',
      lastName: '',
    },
    validationSchema: Yup.object({
      // Same validation as web
    }),
    onSubmit: (values) => {
      dispatch(register(values));
    },
  });

  return (
    <ScrollView className="flex-1 bg-white p-4">
      <View className="space-y-4">
        <TextInput
          mode="outlined"
          label="Email"
          value={formik.values.email}
          onChangeText={formik.handleChange('email')}
          onBlur={formik.handleBlur('email')}
          error={formik.touched.email && !!formik.errors.email}
        />
        <HelperText type="error" visible={formik.touched.email && !!formik.errors.email}>
          {formik.errors.email}
        </HelperText>
        
        {/* Similar fields for other inputs */}
        
        <Button
          mode="contained"
          onPress={() => formik.handleSubmit()}
          className="mt-6"
        >
          Register
        </Button>
      </View>
    </ScrollView>
  );
};

export default RegisterScreen;
```

### 2. Navigation Guard

```typescript
// navigation/AuthNavigator.tsx
import React from 'react';
import { createStackNavigator } from '@react-navigation/stack';
import { useSelector } from 'react-redux';
import { RootState } from '../store';
import LoginScreen from '../screens/auth/LoginScreen';
import RegisterScreen from '../screens/auth/RegisterScreen';
import MainTabNavigator from './MainTabNavigator';

const Stack = createStackNavigator();

const AuthNavigator = () => {
  const { user } = useSelector((state: RootState) => state.auth);

  return (
    <Stack.Navigator screenOptions={{ headerShown: false }}>
      {user ? (
        <Stack.Screen name="Main" component={MainTabNavigator} />
      ) : (
        <>
          <Stack.Screen name="Login" component={LoginScreen} />
          <Stack.Screen name="Register" component={RegisterScreen} />
        </>
      )}
    </Stack.Navigator>
  );
};

export default AuthNavigator;
```

This implementation provides:
- Secure user authentication with JWT
- Age verification for CBD products
- Mobile-responsive design
- Form validation
- Proper error handling
- Persistent authentication state

Would you like me to continue with:
1. Product catalog implementation
2. Shopping cart functionality
3. Checkout process
4. Order tracking system

Let me know which feature you'd like to tackle next!