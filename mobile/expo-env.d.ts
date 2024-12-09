/// <reference types="expo" />
/// <reference types="expo-router/types" />

declare module "*.png" {
  const value: any;
  export default value;
}

declare module "*.jpg" {
  const value: any;
  export default value;
}

declare module "expo-blur" {
  import { ViewProps } from "react-native";
  export type BlurTint = "light" | "dark" | "default" | "systemChromeMaterial";
  export interface BlurViewProps extends ViewProps {
    intensity?: number;
    tint?: BlurTint;
  }
  export class BlurView extends React.Component<BlurViewProps> {}
}

// NOTE: This file should not be edited and should be in your git ignore