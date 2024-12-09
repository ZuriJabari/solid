import React from 'react';
import { Pressable, Text, View, PressableProps } from 'react-native';
import * as Linking from 'expo-linking';

interface ExternalLinkProps extends PressableProps {
  href: string;
  children: React.ReactNode;
}

export function ExternalLink({ href, style, children, ...rest }: ExternalLinkProps) {
  const handlePress = React.useCallback(() => {
    Linking.openURL(href);
  }, [href]);

  return (
    <Pressable
      onPress={handlePress}
      style={style}
      {...rest}
      accessibilityRole="link"
    >
      <Text>{children}</Text>
    </Pressable>
  );
} 