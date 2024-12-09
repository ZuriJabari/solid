import React from 'react';
import { render, fireEvent } from '@testing-library/react-native';
import { HapticTab } from '../../components/HapticTab';
import * as Haptics from 'expo-haptics';

jest.mock('expo-haptics');

describe('HapticTab', () => {
  const mockOnPress = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders children correctly', () => {
    const { getByTestId } = render(
      <HapticTab onPress={mockOnPress}>
        <React.Fragment>Tab Content</React.Fragment>
      </HapticTab>
    );
    
    expect(getByTestId('haptic-tab')).toBeTruthy();
  });

  it('triggers light impact haptic when selected', () => {
    const { getByTestId } = render(
      <HapticTab 
        onPress={mockOnPress}
        accessibilityState={{ selected: true }}
      >
        <React.Fragment>Tab Content</React.Fragment>
      </HapticTab>
    );
    
    fireEvent.press(getByTestId('haptic-tab'));
    expect(Haptics.impactAsync).toHaveBeenCalledWith(Haptics.ImpactFeedbackStyle.Light);
    expect(mockOnPress).toHaveBeenCalled();
  });

  it('triggers selection haptic when not selected', () => {
    const { getByTestId } = render(
      <HapticTab 
        onPress={mockOnPress}
        accessibilityState={{ selected: false }}
      >
        <React.Fragment>Tab Content</React.Fragment>
      </HapticTab>
    );
    
    fireEvent.press(getByTestId('haptic-tab'));
    expect(Haptics.selectionAsync).toHaveBeenCalled();
    expect(mockOnPress).toHaveBeenCalled();
  });
}); 