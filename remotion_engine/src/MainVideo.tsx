// MainVideo.tsx
import React from "react";
import { MotionEngine } from "./MotionEngine";

export const MainVideo: React.FC<{ config: any }> = ({ config }) => {
  // The config is the DSL JSON; MotionEngine interprets it
  return <MotionEngine dsl={config} />;
};