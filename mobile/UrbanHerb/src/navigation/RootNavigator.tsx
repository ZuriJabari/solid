import React from 'react';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import { useSelector } from 'react-redux';
import { RootState } from '../store';
import HomeScreen from '../screens/HomeScreen';
import CartScreen from '../screens/CartScreen';
import ProfileScreen from '../screens/ProfileScreen';
import LoginScreen from '../screens/LoginScreen';
import RegisterScreen from '../screens/RegisterScreen';
import { ROUTES } from '../config/constants';
import { MaterialCommunityIcons } from '@expo/vector-icons';

const Tab = createBottomTabNavigator();
const Stack = createNativeStackNavigator();

const AuthStack = () => (
  <Stack.Navigator screenOptions={{ headerShown: false }}>
    <Stack.Screen name={ROUTES.LOGIN} component={LoginScreen} />
    <Stack.Screen name={ROUTES.REGISTER} component={RegisterScreen} />
  </Stack.Navigator>
);

const TabNavigator = () => (
  <Tab.Navigator
    screenOptions={({ route }) => ({
      tabBarIcon: ({ focused, color, size }) => {
        let iconName;

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
          default:
            iconName = 'help';
        }

        return <MaterialCommunityIcons name={iconName} size={size} color={color} />;
      },
    })}
  >
    <Tab.Screen name={ROUTES.HOME} component={HomeScreen} />
    <Tab.Screen name={ROUTES.CART} component={CartScreen} />
    <Tab.Screen name={ROUTES.PROFILE} component={ProfileScreen} />
  </Tab.Navigator>
);

const RootNavigator = () => {
  const { token } = useSelector((state: RootState) => state.auth);

  return token ? <TabNavigator /> : <AuthStack />;
};

export default RootNavigator; 