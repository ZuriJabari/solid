import { SafeAreaProvider } from 'react-native-safe-area-context';
import { StatusBar } from 'expo-status-bar';
import { ExpoRoot } from 'expo-router';

export default function App() {
  return (
    <SafeAreaProvider>
      <StatusBar style="light" backgroundColor="#5C8B7E" />
      <ExpoRoot context={require.context('./app')} />
    </SafeAreaProvider>
  );
} 