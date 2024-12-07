import React, { useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  FlatList,
  TextInput,
  TouchableOpacity,
  Image,
  ActivityIndicator,
} from 'react-native';
import { useNavigation } from '@react-navigation/native';
import { NativeStackNavigationProp } from '@react-navigation/native-stack';
import { useDispatch, useSelector } from 'react-redux';
import { COLORS } from '../config/constants';
import { 
  fetchProducts,
  fetchProductsByCategory,
  searchProducts,
  setSelectedCategory,
  setSearchQuery,
} from '../store/slices/productSlice';
import type { RootState, AppDispatch } from '../store';
import type { Product } from '../services/productService';

type MarketplaceStackParamList = {
  Marketplace: undefined;
  ProductDetail: { productId: string };
};

type MarketplaceScreenNavigationProp = NativeStackNavigationProp<
  MarketplaceStackParamList,
  'Marketplace'
>;

export const MarketplaceScreen = () => {
  const dispatch = useDispatch<AppDispatch>();
  const navigation = useNavigation<MarketplaceScreenNavigationProp>();
  const {
    products,
    loading,
    error,
    selectedCategory,
    searchQuery,
  } = useSelector((state: RootState) => state.products);

  const categories = ['All', 'Culinary', 'Medicinal', 'Tea', 'Essential Oils'];

  useEffect(() => {
    dispatch(fetchProducts());
  }, [dispatch]);

  const handleSearch = (text: string) => {
    dispatch(setSearchQuery(text));
    if (text.trim()) {
      dispatch(searchProducts(text));
    } else {
      dispatch(fetchProducts());
    }
  };

  const handleCategorySelect = (category: string) => {
    const newCategory = category === selectedCategory ? null : category;
    dispatch(setSelectedCategory(newCategory));
    if (newCategory && newCategory !== 'All') {
      dispatch(fetchProductsByCategory(newCategory));
    } else {
      dispatch(fetchProducts());
    }
  };

  const renderProduct = ({ item }: { item: Product }) => (
    <TouchableOpacity 
      style={styles.productCard}
      onPress={() => navigation.navigate('ProductDetail', { productId: item.id })}
    >
      <Image 
        source={{ uri: item.imageUrl }} 
        style={styles.productImage}
        resizeMode="cover"
      />
      <View style={styles.productInfo}>
        <Text style={styles.productName}>{item.name}</Text>
        <Text style={styles.productPrice}>${item.price.toFixed(2)}</Text>
        {!item.inStock && (
          <Text style={styles.outOfStock}>Out of Stock</Text>
        )}
      </View>
    </TouchableOpacity>
  );

  if (error) {
    return (
      <View style={styles.centered}>
        <Text style={styles.error}>{error}</Text>
        <TouchableOpacity 
          style={styles.retryButton}
          onPress={() => dispatch(fetchProducts())}
        >
          <Text style={styles.retryText}>Retry</Text>
        </TouchableOpacity>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <TextInput
        style={styles.searchInput}
        placeholder="Search herbs..."
        value={searchQuery}
        onChangeText={handleSearch}
      />

      <FlatList
        horizontal
        showsHorizontalScrollIndicator={false}
        data={categories}
        keyExtractor={(item) => item}
        style={styles.categoriesList}
        renderItem={({ item }) => (
          <TouchableOpacity
            style={[
              styles.categoryButton,
              selectedCategory === item && styles.selectedCategory,
            ]}
            onPress={() => handleCategorySelect(item)}
          >
            <Text style={[
              styles.categoryText,
              selectedCategory === item && styles.selectedCategoryText,
            ]}>
              {item}
            </Text>
          </TouchableOpacity>
        )}
      />

      {loading ? (
        <View style={styles.centered}>
          <ActivityIndicator size="large" color={COLORS.primary} />
        </View>
      ) : (
        <FlatList
          data={products}
          renderItem={renderProduct}
          keyExtractor={(item) => item.id}
          numColumns={2}
          showsVerticalScrollIndicator={false}
          contentContainerStyle={styles.productList}
          ListEmptyComponent={
            <View style={styles.emptyState}>
              <Text style={styles.emptyStateText}>No products found</Text>
            </View>
          }
        />
      )}
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: COLORS.background,
    padding: 16,
  },
  centered: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  searchInput: {
    backgroundColor: COLORS.white,
    padding: 12,
    borderRadius: 8,
    marginBottom: 16,
    borderWidth: 1,
    borderColor: COLORS.lightGray,
  },
  categoriesList: {
    marginBottom: 16,
  },
  categoryButton: {
    paddingHorizontal: 16,
    paddingVertical: 8,
    marginRight: 8,
    borderRadius: 20,
    backgroundColor: COLORS.white,
    borderWidth: 1,
    borderColor: COLORS.lightGray,
  },
  selectedCategory: {
    backgroundColor: COLORS.primary,
    borderColor: COLORS.primary,
  },
  categoryText: {
    color: COLORS.text,
    fontSize: 14,
  },
  selectedCategoryText: {
    color: COLORS.white,
  },
  productList: {
    paddingBottom: 16,
  },
  productCard: {
    flex: 1,
    margin: 8,
    backgroundColor: COLORS.white,
    borderRadius: 8,
    overflow: 'hidden',
    elevation: 2,
    shadowColor: COLORS.black,
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
  },
  productImage: {
    width: '100%',
    height: 150,
  },
  productInfo: {
    padding: 8,
  },
  productName: {
    fontSize: 16,
    fontWeight: '600',
    color: COLORS.text,
    marginBottom: 4,
  },
  productPrice: {
    fontSize: 14,
    color: COLORS.primary,
    fontWeight: '600',
  },
  outOfStock: {
    color: COLORS.error,
    fontSize: 12,
    marginTop: 4,
  },
  emptyState: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    paddingVertical: 32,
  },
  emptyStateText: {
    color: COLORS.gray,
    fontSize: 16,
  },
  error: {
    color: COLORS.error,
    fontSize: 16,
    marginBottom: 16,
  },
  retryButton: {
    backgroundColor: COLORS.primary,
    paddingHorizontal: 24,
    paddingVertical: 12,
    borderRadius: 8,
  },
  retryText: {
    color: COLORS.white,
    fontSize: 16,
    fontWeight: '600',
  },
}); 