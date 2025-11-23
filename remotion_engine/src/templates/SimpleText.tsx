import React from 'react';
import {interpolate, useCurrentFrame, useVideoConfig} from 'remotion';

export const SimpleText: React.FC<{text: string; startFrame?: number; endFrame?: number}> = ({text, startFrame = 0, endFrame = 150}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const progress = Math.min(1, Math.max(0, (frame - startFrame) / Math.max(1, (endFrame - startFrame))));

  const y = interpolate(progress, [0, 1], [60, 0]);
  const opacity = interpolate(progress, [0.1, 0.4, 1], [0, 1, 1]);

  return (
    <div style={{flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center'}}>
      <div style={{transform: `translateY(${y}px)`, opacity}}>
        <h1 style={{fontSize: 96, fontFamily: 'Inter, Arial', margin: 0}}>{text}</h1>
      </div>
    </div>
  );
};
