import React from 'react';
import { Text, TextProps, StyleSheet } from 'react-native';
import { useColorScheme } from '../hooks/useColorScheme';

interface ThemedTextProps extends TextProps {
  type?: 'title' | 'subtitle' | 'body';
}

export function ThemedText({ style, type = 'body', ...props }: ThemedTextProps) {
  const colorScheme = useColorScheme();
  const color = colorScheme === 'dark' ? '#FFFFFF' : '#000000';

  return (
    <Text
      style={[
        styles[type],
        { color },
        style,
      ]}
      {...props}
    />
  );
}

const styles = StyleSheet.create({
  title: {
    fontSize: 24,
    fontWeight: 'bold',
  },
  subtitle: {
    fontSize: 18,
    fontWeight: '600',
  },
  body: {
    fontSize: 16,
  },
}); 