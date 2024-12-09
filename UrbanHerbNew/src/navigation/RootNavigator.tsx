import React from 'react';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import { useSelector } from 'react-redux';
import { RootState } from '../store';
import HomeScreen from '../screens/HomeScreen';
import { ROUTES } from '../config/constants';
import { MaterialCommunityIcons } from '@expo/vector-icons';

const Tab = createBottomTabNavigator();
const Stack = createNativeStackNavigator();

const TabNavigator = () => (
  <Tab.Navigator
    screenOptions={({ route }) => ({
      tabBarIcon: ({ focused, color, size }) => {
        let iconName: keyof typeof MaterialCommunityIcons.glyphMap = 'home';

        switch (route.name) {
          case ROUTES.HOME:
            iconName = focused ? 'home' : 'home-outline';
            break;
          case ROUTES.CART:
            iconName = focused ? 'cart' : 'cart-outline';
            break;
          case ROUTES.PROFILE:
            iconName = focused ? 'account' : 'account-outline';
            break;
        }

        return <MaterialCommunityIcons name={iconName} size={size} color={color} />;
      },
    })}
  >
    <Tab.Screen 
      name={ROUTES.HOME} 
      component={HomeScreen}
      options={{
        title: 'Urban Herb',
      }}
    />
  </Tab.Navigator>
);

const RootNavigator = () => {
  // For now, we'll always show the TabNavigator
  // Later we can add authentication logic here
  return <TabNavigator />;
};

export default RootNavigator; 