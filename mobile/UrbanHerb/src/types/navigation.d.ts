import { NavigatorScreenParams } from '@react-navigation/native';

export type RootStackParamList = {
  '(tabs)': NavigatorScreenParams<TabParamList>;
  '(auth)': NavigatorScreenParams<AuthParamList>;
  'modal': undefined;
};

export type TabParamList = {
  'index': undefined;
  'shop': undefined;
  'learn': undefined;
  'profile': undefined;
  'article/[slug]': { slug: string };
  'product/[slug]': { slug: string };
  'category/[slug]': { slug: string };
};

export type AuthParamList = {
  'login': undefined;
  'register': undefined;
};

declare global {
  namespace ReactNavigation {
    interface RootParamList extends RootStackParamList {}
  }
} 