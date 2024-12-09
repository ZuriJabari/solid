import { View, Text, StyleSheet } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

export default function ShopScreen() {
  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.content}>
        <View style={styles.iconContainer}>
          <View style={styles.cart} />
        </View>
        <Text style={styles.title}>Shop</Text>
        <Text style={styles.subtitle}>Browse our natural products</Text>
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#fff',
  },
  content: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    padding: 20,
  },
  iconContainer: {
    width: 100,
    height: 100,
    borderRadius: 50,
    backgroundColor: '#5C8B7E',
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 20,
  },
  cart: {
    width: 50,
    height: 50,
    backgroundColor: '#B5AF9D',
    borderRadius: 25,
  },
  title: {
    fontSize: 24,
    fontWeight: 'bold',
    marginBottom: 10,
    color: '#5C8B7E',
  },
  subtitle: {
    fontSize: 16,
    color: '#B5AF9D',
  },
}); 