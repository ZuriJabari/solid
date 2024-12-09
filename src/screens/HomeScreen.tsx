import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

export function HomeScreen() {
  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.content}>
        <View style={styles.iconContainer}>
          <View style={styles.leaf} />
        </View>
        <Text style={styles.title}>Welcome to UrbanHerb</Text>
        <Text style={styles.subtitle}>Your Natural Health Companion</Text>
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
  leaf: {
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