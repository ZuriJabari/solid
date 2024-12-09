import React from 'react';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { HomeScreen } from '../screens/HomeScreen';
import { ShopScreen } from '../screens/ShopScreen';
import { ProfileScreen } from '../screens/ProfileScreen';
import Ionicons from '@expo/vector-icons/Ionicons';

type TabParamList = {
  Home: undefined;
  Shop: undefined;
  Profile: undefined;
};

const Tab = createBottomTabNavigator<TabParamList>();

export function TabNavigator() {
  return (
    <Tab.Navigator
      screenOptions={({ route }) => ({
        headerShown: true,
        tabBarActiveTintColor: '#5C8B7E',
        tabBarInactiveTintColor: '#B5AF9D',
        tabBarIcon: ({ focused, color, size }) => {
          let iconName: keyof typeof Ionicons.glyphMap;

          if (route.name === 'Home') {
            iconName = focused ? 'home' : 'home-outline';
          } else if (route.name === 'Shop') {
            iconName = focused ? 'cart' : 'cart-outline';
          } else {
            iconName = focused ? 'person' : 'person-outline';
          }

          return <Ionicons name={iconName} size={size} color={color} />;
        },
      })}
    >
      <Tab.Screen 
        name="Home" 
        component={HomeScreen}
        options={{
          title: 'UrbanHerb',
          headerStyle: {
            backgroundColor: '#5C8B7E',
          },
          headerTintColor: '#fff',
          headerTitleStyle: {
            fontWeight: 'bold',
          },
        }}
      />
      <Tab.Screen 
        name="Shop" 
        component={ShopScreen}
        options={{
          headerStyle: {
            backgroundColor: '#5C8B7E',
          },
          headerTintColor: '#fff',
        }}
      />
      <Tab.Screen 
        name="Profile" 
        component={ProfileScreen}
        options={{
          headerStyle: {
            backgroundColor: '#5C8B7E',
          },
          headerTintColor: '#fff',
        }}
      />
    </Tab.Navigator>
  );
} 