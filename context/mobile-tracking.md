# Mobile Order Tracking and Delivery Implementation

## Customer Mobile App

### 1. Order Tracking Screen (screens/orders/OrderTrackingScreen.tsx)
```typescript
import React, { useEffect } from 'react';
import { View, ScrollView, Dimensions } from 'react-native';
import { Text, Surface, ActivityIndicator } from 'react-native-paper';
import { useQuery } from '@tanstack/react-query';
import MapView, { Marker, PROVIDER_GOOGLE } from 'react-native-maps';
import { fetchOrderTracking } from '../../services/api';
import * as Notifications from 'expo-notifications';

const { width } = Dimensions.get('window');

const OrderTrackingScreen = ({ route }) => {
  const { orderNumber } = route.params;
  
  const { data: tracking, isLoading } = useQuery(
    ['orderTracking', orderNumber],
    () => fetchOrderTracking(orderNumber),
    { refetchInterval: 15000 } // Refresh every 15 seconds
  );

  useEffect(() => {
    // Request notification permissions
    const requestPermissions = async () => {
      const { status } = await Notifications.requestPermissionsAsync();
      if (status !== 'granted') {
        Alert.alert('Permission Required', 'Please enable notifications to receive order updates.');
      }
    };

    requestPermissions();
  }, []);

  if (isLoading) return <ActivityIndicator className="flex-1" />;

  const steps = [
    { id: 'CONFIRMED', title: 'Order Confirmed', icon: 'check-circle' },
    { id: 'PROCESSING', title: 'Processing', icon: 'package' },
    { id: 'OUT_FOR_DELIVERY', title: 'Out for Delivery', icon: 'truck' },
    { id: 'DELIVERED', title: 'Delivered', icon: 'flag' },
  ];

  const currentStepIndex = steps.findIndex(step => step.id === tracking.status);

  return (
    <ScrollView className="flex-1 bg-white">
      {/* Order Info Header */}
      <Surface className="p-4 mb-4">
        <Text variant="titleMedium" className="mb-2">Order #{orderNumber}</Text>
        <Text variant="bodyMedium" className="text-gray-600">
          Estimated delivery: {tracking.estimated_delivery_time}
        </Text>
      </Surface>

      {/* Progress Steps */}
      <View className="px-4 mb-4">
        {steps.map((step, index) => (
          <View key={step.id} className="flex-row items-center mb-4">
            <View 
              className={`w-8 h-8 rounded-full items-center justify-center ${
                index <= currentStepIndex ? 'bg-green-500' : 'bg-gray-300'
              }`}
            >
              <Icon 
                name={step.icon} 
                size={20} 
                color={index <= currentStepIndex ? 'white' : 'gray'}
              />
            </View>
            <View className="ml-4 flex-1">
              <Text variant="bodyLarge" 
                className={index <= currentStepIndex ? 'text-black' : 'text-gray-500'}>
                {step.title}
              </Text>
              {tracking.updates[index] && (
                <Text variant="bodySmall" className="text-gray-500">
                  {new Date(tracking.updates[index].timestamp).toLocaleTimeString()}
                </Text>
              )}
            </View>
          </View>
        ))}
      </View>

      {/* Delivery Map */}
      {tracking.status === 'OUT_FOR_DELIVERY' && tracking.delivery_location && (
        <View className="mb-4" style={{ height: width * 0.8 }}>
          <MapView
            provider={PROVIDER_GOOGLE}
            className="flex-1"
            initialRegion={{
              latitude: tracking.delivery_location.latitude,
              longitude: tracking.delivery_location.longitude,
              latitudeDelta: 0.01,
              longitudeDelta: 0.01,
            }}
          >
            <Marker
              coordinate={{
                latitude: tracking.delivery_location.latitude,
                longitude: tracking.delivery_location.longitude,
              }}
              title="Delivery Driver"
            />
            <Marker
              coordinate={{
                latitude: tracking.delivery_address.latitude,
                longitude: tracking.delivery_address.longitude,
              }}
              title="Delivery Address"
              pinColor="blue"
            />
          </MapView>
        </View>
      )}

      {/* Delivery Info */}
      <Surface className="p-4 mb-4">
        <Text variant="titleMedium" className="mb-2">Delivery Details</Text>
        <View className="space-y-2">
          <View className="flex-row justify-between">
            <Text variant="bodyMedium">Status</Text>
            <Text variant="bodyMedium" className="font-medium">
              {tracking.status.replace('_', ' ')}
            </Text>
          </View>
          {tracking.driver && (
            <View className="flex-row justify-between">
              <Text variant="bodyMedium">Driver</Text>
              <Text variant="bodyMedium" className="font-medium">
                {tracking.driver.name}
              </Text>
            </View>
          )}
        </View>
      </Surface>

      {/* Important Notices */}
      <Surface className="p-4 mb-4 bg-yellow-50">
        <Text variant="titleMedium" className="mb-2 text-yellow-800">
          Important Information
        </Text>
        <View className="space-y-2">
          <Text variant="bodyMedium" className="text-yellow-700">
            • Valid ID required for delivery verification
          </Text>
          <Text variant="bodyMedium" className="text-yellow-700">
            • Must be 18 or older to receive delivery
          </Text>
        </View>
      </Surface>
    </ScrollView>
  );
};

export default OrderTrackingScreen;
```

## Delivery Personnel App

### 1. Delivery Tasks Screen (screens/delivery/DeliveryTasksScreen.tsx)
```typescript
import React, { useState } from 'react';
import { View, FlatList } from 'react-native';
import { Text, Surface, Button, Chip } from 'react-native-paper';
import { useQuery } from '@tanstack/react-query';
import { fetchDeliveryTasks } from '../../services/api';

const DeliveryTasksScreen = ({ navigation }) => {
  const [filter, setFilter] = useState('PENDING'); // PENDING, IN_PROGRESS, COMPLETED

  const { data: tasks, isLoading } = useQuery(
    ['deliveryTasks', filter],
    () => fetchDeliveryTasks(filter),
    { refetchInterval: 30000 }
  );

  const renderTask = ({ item }) => (
    <Surface className="mb-4 rounded-lg overflow-hidden">
      <View className="p-4">
        <View className="flex-row justify-between mb-2">
          <Text variant="titleMedium">Order #{item.order_number}</Text>
          <Chip>{item.status}</Chip>
        </View>

        <View className="space-y-2 mb-4">
          <Text variant="bodyMedium" className="text-gray-600">
            {item.delivery_address}
          </Text>
          <Text variant="bodyMedium" className="text-gray-600">
            Items: {item.items_count}
          </Text>
        </View>

        <Button
          mode="contained"
          onPress={() => navigation.navigate('DeliveryDetails', { taskId: item.id })}
        >
          View Details
        </Button>
      </View>
    </Surface>
  );

  return (
    <View className="flex-1 bg-white">
      {/* Filter Chips */}
      <View className="flex-row p-4 space-x-2">
        {['PENDING', 'IN_PROGRESS', 'COMPLETED'].map((status) => (
          <Chip
            key={status}
            selected={filter === status}
            onPress={() => setFilter(status)}
          >
            {status.replace('_', ' ')}
          </Chip>
        ))}
      </View>

      <FlatList
        data={tasks}
        renderItem={renderTask}
        contentContainerStyle={{ padding: 16 }}
        refreshing={isLoading}
        onRefresh={() => refetch()}
      />
    </View>
  );
};

export default DeliveryTasksScreen;
```

### 2. Delivery Details Screen (screens/delivery/DeliveryDetailsScreen.tsx)
```typescript
import React, { useState, useEffect } from 'react';
import { View, ScrollView, Alert } from 'react-native';
import { Text, Button, Surface, TextInput } from 'react-native-paper';
import { useQuery, useMutation } from '@tanstack/react-query';
import MapView, { Marker } from 'react-native-maps';
import * as Location from 'expo-location';
import {
  fetchDeliveryTask,
  updateDeliveryStatus,
  verifyAge,
  updateDeliveryLocation,
} from '../../services/api';

const DeliveryDetailsScreen = ({ route, navigation }) => {
  const { taskId } = route.params;
  const [location, setLocation] = useState(null);
  const [idNumber, setIdNumber] = useState('');

  const { data: task, refetch } = useQuery(
    ['deliveryTask', taskId],
    () => fetchDeliveryTask(taskId)
  );

  const updateStatusMutation = useMutation(updateDeliveryStatus, {
    onSuccess: () => {
      refetch();
      Alert.alert('Success', 'Status updated successfully');
    },
  });

  const verifyAgeMutation = useMutation(verifyAge, {
    onSuccess: () => {
      updateStatusMutation.mutate({ taskId, status: 'COMPLETED' });
    },
  });

  // Start location tracking
  useEffect(() => {
    let locationSubscription;

    const startLocationTracking = async () => {
      const { status } = await Location.requestForegroundPermissionsAsync();
      if (status !== 'granted') {
        Alert.alert('Permission denied');
        return;
      }

      locationSubscription = await Location.watchPositionAsync(
        {
          accuracy: Location.Accuracy.High,
          timeInterval: 10000,
          distanceInterval: 10,
        },
        (location) => {
          setLocation(location.coords);
          updateDeliveryLocation(taskId, location.coords);
        }
      );
    };

    if (task?.status === 'IN_PROGRESS') {
      startLocationTracking();
    }

    return () => {
      if (locationSubscription) {
        locationSubscription.remove();
      }
    };
  }, [task?.status]);

  const handleStartDelivery = () => {
    updateStatusMutation.mutate({ taskId, status: 'IN_PROGRESS' });
  };

  const handleCompleteDelivery = () => {
    if (!idNumber) {
      Alert.alert('ID Required', 'Please enter customer ID number');
      return;
    }

    verifyAgeMutation.mutate({ taskId, idNumber });
  };

  return (
    <ScrollView className="flex-1 bg-white">
      <Surface className="p-4 mb-4">
        <Text variant="titleLarge">Order #{task?.order_number}</Text>
        <Text variant="bodyMedium" className="text-gray-600 mt-2">
          Status: {task?.status.replace('_', ' ')}
        </Text>
      </Surface>

      {/* Map View */}
      {location && (
        <View style={{ height: 300 }} className="mb-4">
          <MapView
            className="flex-1"
            initialRegion={{
              latitude: location.latitude,
              longitude: location.longitude,
              latitudeDelta: 0.01,
              longitudeDelta: 0.01,
            }}
          >
            <Marker coordinate={location} title="Your Location" />
            <Marker
              coordinate={{
                latitude: task.delivery_address.latitude,
                longitude: task.delivery_address.longitude,
              }}
              title="Delivery Address"
              pinColor="blue"
            />
          </MapView>
        </View>
      )}

      {/* Delivery Details */}
      <Surface className="p-4 mb-4">
        <Text variant="titleMedium" className="mb-2">Delivery Details</Text>
        <View className="space-y-2">
          <Text variant="bodyMedium">
            Address: {task?.delivery_address.formatted_address}
          </Text>
          <Text variant="bodyMedium">
            Customer: {task?.customer_name}
          </Text>
          <Text variant="bodyMedium">
            Phone: {task?.customer_phone}
          </Text>
          {task?.delivery_instructions && (
            <Text variant="bodyMedium">
              Instructions: {task.delivery_instructions}
            </Text>
          )}
        </View>
      </Surface>

      {/* Age Verification */}
      {task?.status === 'IN_PROGRESS' && (
        <Surface className="p-4 mb-4">
          <Text variant="titleMedium" className="mb-2">Age Verification</Text>
          <TextInput
            label="ID Number"
            value={idNumber}
            onChangeText={setIdNumber}
            className="mb-2"
          />
          <Text variant="bodySmall" className="text-gray-500 mb-4">
            Please verify customer's age using valid ID
          </Text>
        </Surface>
      )}

      {/* Action Buttons */}
      <View className="p-4">
        {task?.status === 'PENDING' && (
          <Button
            mode="contained"
            onPress={handleStartDelivery}
            className="mb-2"
          >
            Start Delivery
          </Button>
        )}
        
        {task?.status === 'IN_PROGRESS' && (
          <Button
            mode="contained"
            onPress={handleCompleteDelivery}
            className="mb-2"
          >
            Complete Delivery
          </Button>
        )}
      </View>
    </ScrollView>
  );
};

export default DeliveryDetailsScreen;
```

This implementation provides:

1. Customer Features:
- Real-time order tracking
- Live map view of delivery
- Push notifications for updates
- Comprehensive status information
- Important delivery notices

2. Delivery Personnel Features:
- Task management
- Real-time location tracking
- Navigation assistance
- Age verification process
- Delivery status updates
- Customer information access

Next, we can implement:
1. Admin dashboard
2. Analytics system
3. Reporting features
4. Inventory management

Would you like me to proceed with any of these features?