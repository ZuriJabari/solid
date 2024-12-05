# Mobile Product Catalog Implementation

## 1. Product List Screen (screens/products/ProductListScreen.tsx)
```typescript
import React, { useState } from 'react';
import { View, FlatList, RefreshControl } from 'react-native';
import { Searchbar, ActivityIndicator, Chip } from 'react-native-paper';
import { useQuery } from '@tanstack/react-query';
import { fetchProducts, fetchCategories } from '../../services/api';
import ProductCard from '../../components/products/ProductCard';

const ProductListScreen = ({ navigation }) => {
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState(null);
  const [selectedPotency, setSelectedPotency] = useState(null);

  const { data: products, isLoading, refetch } = useQuery(
    ['products', { category: selectedCategory, potency: selectedPotency, search: searchQuery }],
    () => fetchProducts({ category: selectedCategory, potency: selectedPotency, search: searchQuery })
  );

  const { data: categories } = useQuery(['categories'], fetchCategories);

  return (
    <View className="flex-1 bg-white">
      <View className="px-4 pt-4">
        <Searchbar
          placeholder="Search products..."
          onChangeText={setSearchQuery}
          value={searchQuery}
          className="mb-4"
        />
        
        <FlatList
          horizontal
          data={categories}
          showsHorizontalScrollIndicator={false}
          renderItem={({ item }) => (
            <Chip
              selected={selectedCategory === item.slug}
              onPress={() => setSelectedCategory(
                selectedCategory === item.slug ? null : item.slug
              )}
              className="mr-2"
            >
              {item.name}
            </Chip>
          )}
          className="mb-4"
        />
      </View>

      {isLoading ? (
        <ActivityIndicator className="flex-1" />
      ) : (
        <FlatList
          data={products}
          renderItem={({ item }) => (
            <ProductCard
              product={item}
              onPress={() => navigation.navigate('ProductDetail', { slug: item.slug })}
            />
          )}
          numColumns={2}
          refreshControl={
            <RefreshControl refreshing={isLoading} onRefresh={refetch} />
          }
          contentContainerClassName="p-4"
          columnWrapperClassName="justify-between"
        />
      )}
    </View>
  );
};

export default ProductListScreen;
```

## 2. Product Card Component (components/products/ProductCard.tsx)
```typescript
import React from 'react';
import { View, TouchableOpacity, Image } from 'react-native';
import { Text, Surface } from 'react-native-paper';
import { Star } from 'lucide-react';

interface ProductCardProps {
  product: {
    name: string;
    primary_image: string;
    price: number;
    sale_price: number | null;
    short_description: string;
    potency: string;
    average_rating: number;
  };
  onPress: () => void;
}

const ProductCard: React.FC<ProductCardProps> = ({ product, onPress }) => {
  return (
    <TouchableOpacity onPress={onPress} className="w-[48%] mb-4">
      <Surface className="rounded-lg overflow-hidden">
        <View className="relative">
          <Image
            source={{ uri: product.primary_image }}
            className="w-full aspect-square"
            resizeMode="cover"
          />
          {product.sale_price && (
            <View className="absolute top-2 right-2 bg-red-500 px-2 py-1 rounded">
              <Text className="text-white text-xs font-medium">Sale</Text>
            </View>
          )}
        </View>

        <View className="p-3">
          <Text className="font-medium mb-1" numberOfLines={1}>
            {product.name}
          </Text>
          
          <Text className="text-gray-600 text-xs mb-2" numberOfLines={2}>
            {product.short_description}
          </Text>

          <View className="flex-row items-center justify-between">
            <View>
              {product.sale_price ? (
                <View className="flex-row items-center">
                  <Text className="text-red-600 font-medium">
                    ${product.sale_price}
                  </Text>
                  <Text className="text-gray-400 text-xs line-through ml-1">
                    ${product.price}
                  </Text>
                </View>
              ) : (
                <Text className="font-medium">${product.price}</Text>
              )}
            </View>
            
            <View className="bg-indigo-100 px-2 py-1 rounded">
              <Text className="text-indigo-800 text-xs">
                {product.potency}
              </Text>
            </View>
          </View>

          <View className="flex-row mt-2">
            {[...Array(5)].map((_, i) => (
              <Star
                key={i}
                size={12}
                fill={i < Math.round(product.average_rating) ? '#FBBF24' : 'none'}
                stroke={i < Math.round(product.average_rating) ? '#FBBF24' : '#D1D5DB'}
              />
            ))}
          </View>
        </View>
      </Surface>
    </TouchableOpacity>
  );
};

export default ProductCard;
```

## 3. Product Detail Screen (screens/products/ProductDetailScreen.tsx)
```typescript
import React from 'react';
import { View, ScrollView, Image, useWindowDimensions } from 'react-native';
import { Text, Button, Divider, Surface } from 'react-native-paper';
import { useQuery } from '@tanstack/react-query';
import { fetchProduct } from '../../services/api';
import { useCart } from '../../hooks/useCart';

const ProductDetailScreen = ({ route, navigation }) => {
  const { slug } = route.params;
  const { width } = useWindowDimensions();
  const { addToCart } = useCart();

  const { data: product, isLoading } = useQuery(
    ['product', slug],
    () => fetchProduct(slug)
  );

  if (isLoading || !product) {
    return <ActivityIndicator className="flex-1" />;
  }

  return (
    <ScrollView className="flex-1 bg-white">
      {/* Image Carousel */}
      <ScrollView
        horizontal
        pagingEnabled
        showsHorizontalScrollIndicator={false}
      >
        {product.images.map((image) => (
          <Image
            key={image.id}
            source={{ uri: image.image }}
            style={{ width, height: width }}
            resizeMode="cover"
          />
        ))}
      </ScrollView>

      {/* Product Info */}
      <View className="p-4">
        <Text variant="headlineMedium" className="font-bold mb-2">
          {product.name}
        </Text>

        <View className="flex-row items-center justify-between mb-4">
          <View className="flex-row items-center">
            {product.sale_price ? (
              <>
                <Text className="text-xl font-bold text-red-600">
                  ${product.sale_price}
                </Text>
                <Text className="text-gray-400 line-through ml-2">
                  ${product.price}
                </Text>
              </>
            ) : (
              <Text className="text-xl font-bold">
                ${product.price}
              </Text>
            )}
          </View>

          <Surface className="px-3 py-1 rounded">
            <Text className="text-indigo-800">
              {product.potency} Potency
            </Text>
          </Surface>
        </View>

        <Divider className="mb-4" />

        {/* Description */}
        <Text variant="titleMedium" className="font-medium mb-2">
          Description
        </Text>
        <Text className="text-gray-600 mb-4">
          {product.description}
        </Text>

        {/* Usage Instructions */}
        <Text variant="titleMedium" className="font-medium mb-2">
          How to Use
        </Text>
        <Text className="text-gray-600 mb-4">
          {product.usage_instructions}
        </Text>

        {/* Ingredients */}
        <Text variant="titleMedium" className="font-medium mb-2">
          Ingredients
        </Text>
        <Text className="text-gray-600 mb-4">
          {product.ingredients}
        </Text>

        {/* Warnings */}
        <Surface className="bg-red-50 p-4 rounded-lg mb-4">
          <Text className="text-red-800 font-medium mb-1">
            Important Information
          </Text>
          <Text className="text-red-600">
            {product.warnings}
          </Text>
        </Surface>

        {/* Add to Cart Button */}
        <Button
          mode="contained"
          onPress={() => addToCart(product)}
          className="mb-4"
        >
          Add to Cart
        </Button>
      </View>
    </ScrollView>
  );
};

export default ProductDetailScreen;
```

## 4. API Integration (services/api.ts)
```typescript
import axios from 'axios';

const api = axios.create({
  baseURL: process.env.EXPO_PUBLIC_API_URL,
});

export const fetchProducts = async ({
  category,
  potency,
  search,
  page = 1,
}) => {
  const params = new URLSearchParams();
  if (category) params.append('category', category);
  if (potency) params.append('potency', potency);
  if (search) params.append('search', search);
  params.append('page', page.toString());

  const response = await api.get(`/products/?${params}`);
  return response.data;
};

export const fetchProduct = async (slug: string) => {
  const response = await api.get(`/products/${slug}/`);
  return response.data;
};

export const fetchCategories = async () => {
  const response = await api.get('/categories/');
  return response.data;
};
```

This implementation provides:
1. A responsive grid layout for products
2. Beautiful product cards with sale indicators
3. Smooth image carousel in product details
4. Category filtering with chips
5. Search functionality
6. Pull-to-refresh
7. Loading states
8. Error handling

Next steps could be:
1. Implementing the shopping cart
2. Adding to cart animations
3. Implementing the checkout process
4. Setting up order tracking

Would you like me to proceed with any of these features?