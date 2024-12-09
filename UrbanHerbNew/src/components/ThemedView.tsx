import React from 'react';
import { View, ViewProps } from 'react-native';
import { useColorScheme } from '../hooks/useColorScheme';

export function ThemedView({ style, ...props }: ViewProps) {
  const colorScheme = useColorScheme();
  const backgroundColor = colorScheme === 'dark' ? '#000000' : '#FFFFFF';

  return (
    <View
      style={[
        { backgroundColor },
        style,
      ]}
      {...props}
    />
  );
} 