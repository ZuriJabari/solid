import React from 'react';
import { render, fireEvent } from '@testing-library/react-native';
import { ExternalLink } from '../../components/ExternalLink';
import * as Linking from 'expo-linking';

jest.mock('expo-linking');

describe('ExternalLink', () => {
  it('renders correctly', () => {
    const { getByText } = render(
      <ExternalLink href="https://example.com">
        Test Link
      </ExternalLink>
    );
    
    expect(getByText('Test Link')).toBeTruthy();
  });

  it('opens URL when pressed', () => {
    const url = 'https://example.com';
    const { getByText } = render(
      <ExternalLink href={url}>
        Test Link
      </ExternalLink>
    );
    
    fireEvent.press(getByText('Test Link'));
    expect(Linking.openURL).toHaveBeenCalledWith(url);
  });
}); 