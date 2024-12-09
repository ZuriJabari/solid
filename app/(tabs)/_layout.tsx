import { Tabs } from 'expo-router';
import { useColorScheme } from 'react-native';
import Ionicons from '@expo/vector-icons/Ionicons';

export default function TabLayout() {
  const colorScheme = useColorScheme();

  return (
    <Tabs
      screenOptions={{
        headerStyle: {
          backgroundColor: '#5C8B7E',
        },
        headerTintColor: '#fff',
        tabBarActiveTintColor: '#5C8B7E',
        tabBarInactiveTintColor: '#B5AF9D',
      }}
    >
      <Tabs.Screen
        name="index"
        options={{
          title: 'UrbanHerb',
          tabBarIcon: ({ color, size }) => (
            <Ionicons name="home" size={size} color={color} />
          ),
        }}
      />
      <Tabs.Screen
        name="shop"
        options={{
          title: 'Shop',
          tabBarIcon: ({ color, size }) => (
            <Ionicons name="cart" size={size} color={color} />
          ),
        }}
      />
      <Tabs.Screen
        name="profile"
        options={{
          title: 'Profile',
          tabBarIcon: ({ color, size }) => (
            <Ionicons name="person" size={size} color={color} />
          ),
        }}
      />
    </Tabs>
  );
} 