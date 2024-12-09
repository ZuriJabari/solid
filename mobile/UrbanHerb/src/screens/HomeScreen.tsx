import React, { useEffect, useState } from 'react';
import { View, StyleSheet, FlatList, RefreshControl } from 'react-native';
import { Text, Card, Title, Paragraph } from 'react-native-paper';
import { fetchHerbs } from '../services/api';
import { SafeAreaView } from 'react-native-safe-area-context';

interface Herb {
  id: number;
  name: string;
  description: string;
  price: number;
  image: string;
}

const HomeScreen = () => {
  const [herbs, setHerbs] = useState<Herb[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadHerbs = async () => {
    try {
      const data = await fetchHerbs();
      setHerbs(data);
      setError(null);
    } catch (err) {
      setError('Failed to load herbs. Please try again.');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    loadHerbs();
  }, []);

  const onRefresh = () => {
    setRefreshing(true);
    loadHerbs();
  };

  const renderHerbCard = ({ item }: { item: Herb }) => (
    <Card style={styles.card}>
      {item.image && <Card.Cover source={{ uri: item.image }} />}
      <Card.Content>
        <Title>{item.name}</Title>
        <Paragraph>{item.description}</Paragraph>
        <Text style={styles.price}>${item.price.toFixed(2)}</Text>
      </Card.Content>
    </Card>
  );

  if (loading && !refreshing) {
    return (
      <View style={styles.centered}>
        <Text>Loading herbs...</Text>
      </View>
    );
  }

  if (error && !refreshing) {
    return (
      <View style={styles.centered}>
        <Text style={styles.error}>{error}</Text>
      </View>
    );
  }

  return (
    <SafeAreaView style={styles.container}>
      <FlatList
        data={herbs}
        renderItem={renderHerbCard}
        keyExtractor={(item) => item.id.toString()}
        contentContainerStyle={styles.list}
        refreshControl={
          <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
        }
      />
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f5f5f5',
  },
  list: {
    padding: 16,
  },
  card: {
    marginBottom: 16,
    elevation: 4,
  },
  price: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#2e7d32',
    marginTop: 8,
  },
  centered: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  error: {
    color: '#d32f2f',
    textAlign: 'center',
  },
});

export default HomeScreen; 