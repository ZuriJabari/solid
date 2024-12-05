# Shopping Cart Implementation

## 1. Cart State Management

### Redux Store (src/store/cartSlice.ts)
```typescript
import { createSlice, PayloadAction } from '@reduxjs/toolkit';
import AsyncStorage from '@react-native-async-storage/async-storage';

interface CartItem {
  id: number;
  name: string;
  price: number;
  sale_price: number | null;
  quantity: number;
  image: string;
  stock: number;
  weight: number;
}

interface CartState {
  items: CartItem[];
  loading: boolean;
  error: string | null;
}

const initialState: CartState = {
  items: [],
  loading: false,
  error: null,
};

const cartSlice = createSlice({
  name: 'cart',
  initialState,
  reducers: {
    addToCart: (state, action: PayloadAction<CartItem>) => {
      const existingItem = state.items.find(item => item.id === action.payload.id);
      
      if (existingItem) {
        // Check stock limit
        const newQuantity = existingItem.quantity + 1;
        if (newQuantity <= action.payload.stock) {
          existingItem.quantity = newQuantity;
        }
      } else {
        state.items.push({ ...action.payload, quantity: 1 });
      }
      
      // Save to AsyncStorage
      AsyncStorage.setItem('cart', JSON.stringify(state.items));
    },
    
    removeFromCart: (state, action: PayloadAction<number>) => {
      state.items = state.items.filter(item => item.id !== action.payload);
      AsyncStorage.setItem('cart', JSON.stringify(state.items));
    },
    
    updateQuantity: (state, action: PayloadAction<{ id: number; quantity: number }>) => {
      const item = state.items.find(item => item.id === action.payload.id);
      if (item && action.payload.quantity <= item.stock && action.payload.quantity > 0) {
        item.quantity = action.payload.quantity;
        AsyncStorage.setItem('cart', JSON.stringify(state.items));
      }
    },
    
    clearCart: (state) => {
      state.items = [];
      AsyncStorage.removeItem('cart');
    },
    
    loadCart: (state, action: PayloadAction<CartItem[]>) => {
      state.items = action.payload;
    },
  },
});

export const { addToCart, removeFromCart, updateQuantity, clearCart, loadCart } = cartSlice.actions;
export default cartSlice.reducer;

// Selectors
export const selectCartItems = (state: RootState) => state.cart.items;
export const selectCartTotal = (state: RootState) => 
  state.cart.items.reduce((total, item) => {
    const price = item.sale_price || item.price;
    return total + (price * item.quantity);
  }, 0);
export const selectCartItemsCount = (state: RootState) =>
  state.cart.items.reduce((count, item) => count + item.quantity, 0);
```

### Cart Hook (src/hooks/useCart.ts)
```typescript
import { useEffect } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { addToCart, removeFromCart, updateQuantity, clearCart, loadCart } from '../store/cartSlice';

export const useCart = () => {
  const dispatch = useDispatch();
  const cartItems = useSelector(selectCartItems);
  const cartTotal = useSelector(selectCartTotal);
  const itemsCount = useSelector(selectCartItemsCount);

  useEffect(() => {
    const loadSavedCart = async () => {
      try {
        const savedCart = await AsyncStorage.getItem('cart');
        if (savedCart) {
          dispatch(loadCart(JSON.parse(savedCart)));
        }
      } catch (error) {
        console.error('Error loading cart:', error);
      }
    };

    loadSavedCart();
  }, [dispatch]);

  return {
    cartItems,
    cartTotal,
    itemsCount,
    addItem: (product: Product) => dispatch(addToCart(product)),
    removeItem: (productId: number) => dispatch(removeFromCart(productId)),
    updateItemQuantity: (productId: number, quantity: number) =>
      dispatch(updateQuantity({ id: productId, quantity })),
    clearCart: () => dispatch(clearCart()),
  };
};
```

## 2. Cart Components (Web)

### Cart Drawer (src/components/cart/CartDrawer.tsx)
```typescript
import React from 'react';
import { Dialog, Transition } from '@headlessui/react';
import { XMarkIcon } from '@heroicons/react/24/outline';
import { useCart } from '../../hooks/useCart';
import CartItem from './CartItem';
import { formatCurrency } from '../../utils/format';

interface CartDrawerProps {
  isOpen: boolean;
  onClose: () => void;
}

const CartDrawer: React.FC<CartDrawerProps> = ({ isOpen, onClose }) => {
  const { cartItems, cartTotal, itemsCount } = useCart();

  return (
    <Transition.Root show={isOpen} as={React.Fragment}>
      <Dialog as="div" className="relative z-50" onClose={onClose}>
        <div className="fixed inset-0 bg-black bg-opacity-25" />

        <div className="fixed inset-0 overflow-hidden">
          <div className="absolute inset-0 overflow-hidden">
            <div className="pointer-events-none fixed inset-y-0 right-0 flex max-w-full pl-10">
              <Transition.Child
                enter="transform transition ease-in-out duration-500"
                enterFrom="translate-x-full"
                enterTo="translate-x-0"
                leave="transform transition ease-in-out duration-500"
                leaveFrom="translate-x-0"
                leaveTo="translate-x-full"
              >
                <Dialog.Panel className="pointer-events-auto w-screen max-w-md">
                  <div className="flex h-full flex-col bg-white shadow-xl">
                    <div className="flex-1 overflow-y-auto py-6 px-4 sm:px-6">
                      <div className="flex items-start justify-between">
                        <Dialog.Title className="text-lg font-medium text-gray-900">
                          Shopping Cart ({itemsCount} items)
                        </Dialog.Title>
                        <button
                          type="button"
                          className="relative -m-2 p-2 text-gray-400 hover:text-gray-500"
                          onClick={onClose}
                        >
                          <XMarkIcon className="h-6 w-6" aria-hidden="true" />
                        </button>
                      </div>

                      <div className="mt-8">
                        <div className="flow-root">
                          <ul className="-my-6 divide-y divide-gray-200">
                            {cartItems.map((item) => (
                              <CartItem key={item.id} item={item} />
                            ))}
                          </ul>
                        </div>
                      </div>
                    </div>

                    <div className="border-t border-gray-200 py-6 px-4 sm:px-6">
                      <div className="flex justify-between text-base font-medium text-gray-900">
                        <p>Subtotal</p>
                        <p>{formatCurrency(cartTotal)}</p>
                      </div>
                      <p className="mt-0.5 text-sm text-gray-500">
                        Shipping and taxes calculated at checkout
                      </p>
                      <div className="mt-6">
                        <button
                          onClick={() => {
                            onClose();
                            // Navigate to checkout
                          }}
                          className="flex w-full items-center justify-center rounded-md border border-transparent bg-indigo-600 px-6 py-3 text-base font-medium text-white shadow-sm hover:bg-indigo-700"
                        >
                          Checkout
                        </button>
                      </div>
                      <div className="mt-6 flex justify-center text-center text-sm text-gray-500">
                        <p>
                          or{' '}
                          <button
                            type="button"
                            className="font-medium text-indigo-600 hover:text-indigo-500"
                            onClick={onClose}
                          >
                            Continue Shopping
                          </button>
                        </p>
                      </div>
                    </div>
                  </div>
                </Dialog.Panel>
              </Transition.Child>
            </div>
          </div>
        </div>
      </Dialog>
    </Transition.Root>
  );
};

export default CartDrawer;
```

## 3. Cart Components (Mobile)

### Cart Screen (screens/cart/CartScreen.tsx)
```typescript
import React from 'react';
import { View, ScrollView } from 'react-native';
import { Text, Button, Divider } from 'react-native-paper';
import { useCart } from '../../hooks/useCart';
import CartItem from '../../components/cart/CartItem';
import { formatCurrency } from '../../utils/format';

const CartScreen = ({ navigation }) => {
  const { cartItems, cartTotal, itemsCount } = useCart();

  if (itemsCount === 0) {
    return (
      <View className="flex-1 justify-center items-center p-4">
        <Text variant="headlineSmall" className="mb-4">Your cart is empty</Text>
        <Button
          mode="contained"
          onPress={() => navigation.navigate('Products')}
        >
          Start Shopping
        </Button>
      </View>
    );
  }

  return (
    <View className="flex-1 bg-white">
      <ScrollView className="flex-1">
        <View className="p-4">
          <Text variant="titleLarge" className="mb-4">
            Shopping Cart ({itemsCount} items)
          </Text>

          <View className="space-y-4">
            {cartItems.map((item) => (
              <CartItem key={item.id} item={item} />
            ))}
          </View>
        </View>
      </ScrollView>

      <View className="border-t border-gray-200 p-4">
        <View className="flex-row justify-between mb-2">
          <Text variant="bodyLarge">Subtotal</Text>
          <Text variant="bodyLarge" className="font-bold">
            {formatCurrency(cartTotal)}
          </Text>
        </View>
        
        <Text variant="bodySmall" className="text-gray-500 mb-4">
          Shipping and taxes calculated at checkout
        </Text>

        <Button
          mode="contained"
          onPress={() => navigation.navigate('Checkout')}
          className="mb-2"
        >
          Proceed to Checkout
        </Button>
        
        <Button
          mode="outlined"
          onPress={() => navigation.goBack()}
        >
          Continue Shopping
        </Button>
      </View>
    </View>
  );
};

export default CartScreen;
```

### Cart Item Component (components/cart/CartItem.tsx)
```typescript
import React from 'react';
import { View, Image } from 'react-native';
import { Text, IconButton, TextInput, Surface } from 'react-native-paper';
import { useCart } from '../../hooks/useCart';
import { formatCurrency } from '../../utils/format';

const CartItem = ({ item }) => {
  const { updateItemQuantity, removeItem } = useCart();

  return (
    <Surface className="rounded-lg overflow-hidden">
      <View className="flex-row p-4">
        <Image
          source={{ uri: item.image }}
          className="w-20 h-20 rounded"
        />
        
        <View className="flex-1 ml-4">
          <View className="flex-row justify-between">
            <Text variant="titleMedium" numberOfLines={1}>
              {item.name}
            </Text>
            <IconButton
              icon="close"
              size={20}
              onPress={() => removeItem(item.id)}
            />
          </View>

          <Text variant="bodyMedium" className="text-gray-600">
            {formatCurrency(item.sale_price || item.price)}
          </Text>

          <View className="flex-row items-center mt-2">
            <IconButton
              icon="minus"
              size={20}
              onPress={() => updateItemQuantity(item.id, item.quantity - 1)}
              disabled={item.quantity === 1}
            />
            <TextInput
              value={String(item.quantity)}
              onChangeText={(text) => {
                const quantity = parseInt(text);
                if (!isNaN(quantity)) {
                  updateItemQuantity(item.id, quantity);
                }
              }}
              keyboardType="numeric"
              className="w-12 text-center"
            />
            <IconButton
              icon="plus"
              size={20}
              onPress={() => updateItemQuantity(item.id, item.quantity + 1)}
              disabled={item.quantity === item.stock}
            />
          </View>
        </View>
      </View>
    </Surface>
  );
};

export default CartItem;
```

This implementation provides:

1. Persistent cart state using Redux and AsyncStorage
2. Real-time cart updates
3. Quantity validation against stock levels
4. Beautiful UI for both web and mobile
5. Smooth animations for cart interactions
6. Price calculations including sale prices
7. Cart summary with subtotal

Next steps could be:
1. Implementing the checkout process
2. Adding delivery options selection
3. Integrating payment processing
4. Setting up order confirmation

Would you like me to continue with any of these features?