"use client";

import { Check } from "lucide-react";

interface Iteration {
  number: number;
  type: string;
  resultsCount: number;
}

interface IterationTimelineProps {
  iterations: Iteration[];
  currentIteration: number;
  onSelectIteration?: (iteration: number) => void;
}

export function IterationTimeline({
  iterations,
  currentIteration,
  onSelectIteration,
}: IterationTimelineProps) {
  if (iterations.length === 0) {
    return null;
  }

  return (
    <div className="glass-card p-4">
      <h3 className="font-semibold text-text-primary mb-4">Search Journey</h3>
      
      <div className="relative">
        {/* Connection line */}
        <div className="absolute top-4 left-4 right-4 h-0.5 bg-border" />
        
        {/* Iterations */}
        <div className="relative flex justify-between">
          {iterations.map((iteration, index) => {
            const isActive = iteration.number === currentIteration;
            const isCompleted = iteration.number < currentIteration;
            
            return (
              <div
                key={iteration.number}
                className="flex flex-col items-center"
                onClick={() => onSelectIteration?.(iteration.number)}
              >
                <div
                  className={`
                    iteration-dot cursor-pointer
                    ${isActive ? "active" : ""}
                    ${isCompleted ? "completed" : ""}
                    ${!isActive && !isCompleted ? "pending" : ""}
                  `}
                >
                  {isCompleted ? (
                    <Check className="w-4 h-4" />
                  ) : (
                    iteration.number
                  )}
                </div>
                
                <div className="mt-2 text-center">
                  <p className={`text-xs font-medium ${isActive ? "text-accent" : "text-text-secondary"}`}>
                    {getTypeLabel(iteration.type)}
                  </p>
                  <p className="text-xs text-text-muted">
                    {iteration.resultsCount} results
                  </p>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}

function getTypeLabel(type: string): string {
  switch (type) {
    case "text":
      return "Text";
    case "image":
      return "Image";
    case "feedback":
      return "Feedback";
    case "pseudo_feedback":
      return "Auto";
    default:
      return type;
  }
}

