"use client";

import { useMemo } from "react";
import type { QueryVector } from "@/lib/api";

interface VectorVisualizationProps {
  queryVectors: QueryVector[];
  corpusVectors?: { x: number; y: number }[];
  width?: number;
  height?: number;
}

export function VectorVisualization({
  queryVectors,
  corpusVectors = [],
  width = 320,
  height = 240,
}: VectorVisualizationProps) {
  // Calculate bounds and scaling
  const { scale, offsetX, offsetY, pathD } = useMemo(() => {
    const allPoints = [
      ...queryVectors.map((v) => ({ x: v.x, y: v.y })),
      ...corpusVectors,
    ];

    if (allPoints.length === 0) {
      return { scale: 1, offsetX: width / 2, offsetY: height / 2, pathD: "" };
    }

    const xs = allPoints.map((p) => p.x);
    const ys = allPoints.map((p) => p.y);
    
    const minX = Math.min(...xs);
    const maxX = Math.max(...xs);
    const minY = Math.min(...ys);
    const maxY = Math.max(...ys);
    
    // Add a minimum range to handle very close or identical points
    let rangeX = maxX - minX;
    let rangeY = maxY - minY;
    
    // If range is too small, add some padding to ensure visibility
    const minRange = 0.1;
    if (rangeX < minRange) rangeX = minRange;
    if (rangeY < minRange) rangeY = minRange;
    
    // Increase padding to ensure points are never cut off
    const padding = 50;
    const scaleX = (width - padding * 2) / rangeX;
    const scaleY = (height - padding * 2) / rangeY;
    const scale = Math.min(scaleX, scaleY);
    
    const centerX = (minX + maxX) / 2;
    const centerY = (minY + maxY) / 2;
    
    const offsetX = width / 2 - centerX * scale;
    const offsetY = height / 2 + centerY * scale; // Flip Y

    // Create path for query trajectory
    const pathD = queryVectors.length > 1
      ? queryVectors
          .map((v, i) => {
            const x = v.x * scale + offsetX;
            const y = -v.y * scale + offsetY;
            return i === 0 ? `M ${x} ${y}` : `L ${x} ${y}`;
          })
          .join(" ")
      : "";

    return { scale, offsetX, offsetY, pathD };
  }, [queryVectors, corpusVectors, width, height]);

  if (queryVectors.length === 0) {
    return (
      <div className="glass-card overflow-hidden">
        <div className="p-4 border-b border-border">
          <h3 className="font-semibold text-text-primary">Query Vector Space</h3>
          <p className="text-sm text-text-muted">
            Vector visualization will appear after search
          </p>
        </div>
        <div className="flex items-center justify-center" style={{ height: height }}>
          <p className="text-text-muted text-sm">No data yet</p>
        </div>
      </div>
    );
  }

  return (
    <div className="glass-card overflow-hidden">
      <div className="p-4 border-b border-border">
        <h3 className="font-semibold text-text-primary">Query Vector Space</h3>
        <p className="text-sm text-text-muted">
          Tracking query movement across {queryVectors.length} iteration{queryVectors.length !== 1 ? "s" : ""}
        </p>
      </div>
      
      <div className="p-4">
        <style>{`
          .hover-shake:hover {
            animation: shake 0.3s ease-in-out infinite;
          }
          
          @keyframes shake {
            0%, 100% { transform: translate(0, 0); }
            25% { transform: translate(-2px, -2px); }
            50% { transform: translate(2px, 2px); }
            75% { transform: translate(-2px, 2px); }
          }
        `}</style>
        <svg width={width} height={height} className="block">
          {/* Background grid */}
          <defs>
            <pattern id="grid" width="20" height="20" patternUnits="userSpaceOnUse">
              <path
                d="M 20 0 L 0 0 0 20"
                fill="none"
                stroke="var(--border)"
                strokeWidth="0.5"
              />
            </pattern>
          </defs>
          <rect width="100%" height="100%" fill="url(#grid)" opacity="0.3" />

          {/* Corpus vectors (background) */}
          {corpusVectors.map((point, i) => {
            const x = point.x * scale + offsetX;
            const y = -point.y * scale + offsetY;
            return (
              <circle
                key={`corpus-${i}`}
                cx={x}
                cy={y}
                r={3}
                fill="var(--viz-corpus)"
                opacity={0.2}
              />
            );
          })}

          {/* Query trajectory path */}
          {pathD && (
            <path
              d={pathD}
              fill="none"
              stroke="var(--viz-query)"
              strokeWidth="2"
              strokeDasharray="4 4"
              className="viz-path"
              opacity={0.6}
            />
          )}

          {/* Query vectors */}
          {queryVectors.map((vector, i) => {
            const x = vector.x * scale + offsetX;
            const y = -vector.y * scale + offsetY;
            const isLatest = i === queryVectors.length - 1;
            
            return (
              <g key={`query-${i}`} className="viz-dot cursor-pointer hover-shake" style={{ transformOrigin: `${x}px ${y}px` }}>
                {/* Glow for latest */}
                {isLatest && (
                  <circle
                    cx={x}
                    cy={y}
                    r={16}
                    fill="var(--viz-query)"
                    opacity={0.15}
                    className="animate-pulse-glow"
                  />
                )}
                
                {/* Main dot */}
                <circle
                  cx={x}
                  cy={y}
                  r={isLatest ? 10 : 6}
                  fill={isLatest ? "var(--viz-query)" : "var(--surface-elevated)"}
                  stroke="var(--viz-query)"
                  strokeWidth={2}
                  className="transition-all"
                />
                
                {/* Iteration number */}
                <text
                  x={x}
                  y={y}
                  textAnchor="middle"
                  dominantBaseline="central"
                  fill={isLatest ? "white" : "var(--viz-query)"}
                  fontSize={isLatest ? "12" : "10"}
                  fontWeight="600"
                  pointerEvents="none"
                >
                  {vector.iteration}
                </text>
              </g>
            );
          })}

          {/* Legend */}
          <g transform={`translate(10, ${height - 50})`}>
            <rect
              x={0}
              y={0}
              width={110}
              height={45}
              fill="var(--surface)"
              rx={8}
              opacity={0.9}
            />
            <circle cx={15} cy={15} r={5} fill="var(--viz-query)" />
            <text x={28} y={19} fill="var(--text-secondary)" fontSize="11">
              Query Vector
            </text>
            {corpusVectors.length > 0 && (
              <>
                <circle cx={15} cy={33} r={4} fill="var(--viz-corpus)" opacity={0.5} />
                <text x={28} y={37} fill="var(--text-secondary)" fontSize="11">
                  Corpus Sample
                </text>
              </>
            )}
          </g>
        </svg>
      </div>
    </div>
  );
}
