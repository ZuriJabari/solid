import React from 'react';
import { View, Pressable, Text, StyleSheet } from 'react-native';
import * as Haptics from 'expo-haptics';
import { BottomTabBarButtonProps } from '@react-navigation/bottom-tabs';

export function HapticTab(props: BottomTabBarButtonProps) {
  const { children, accessibilityState, onPress } = props;
  
  const handlePress = React.useCallback(() => {
    const isSelected = accessibilityState?.selected;
    if (isSelected) {
      Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
    } else {
      Haptics.selectionAsync().catch(console.error);
    }
    onPress?.();
  }, [accessibilityState?.selected, onPress]);

  return (
    <Pressable
      testID="haptic-tab"
      onPress={handlePress}
      style={({ pressed }) => [
        styles.tab,
        pressed && styles.pressed
      ]}
    >
      {children}
    </Pressable>
  );
}

const styles = StyleSheet.create({
  tab: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 8,
  },
  pressed: {
    opacity: 0.7,
  },
}); 