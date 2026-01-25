// frontend/src/components/idea-canvas/ApproachPanel.tsx

"use client";

import { Approach, RefinementTarget } from "@/lib/types/idea-canvas";
import { MermaidDiagram } from "./MermaidDiagram";
import { TaskTable } from "./TaskTable";

interface ApproachPanelProps {
  approach: Approach;
  approachIndex: number;
  onElementClick?: (target: RefinementTarget) => void;
  refinementTarget?: RefinementTarget;
}

export function ApproachPanel({
  approach,
  approachIndex,
  onElementClick,
  refinementTarget,
}: ApproachPanelProps) {
  const isHighlightedApproach = refinementTarget?.approachIndex === approachIndex;

  const handleDiagramClick = (elementId: string) => {
    onElementClick?.({
      approachIndex,
      elementId,
      elementType: "diagram",
    });
  };

  const handleTaskClick = (taskId: string) => {
    onElementClick?.({
      approachIndex,
      elementId: taskId,
      elementType: "task",
    });
  };

  return (
    <div className="h-full flex gap-4 p-4">
      {/* Mermaid Diagram - Left Half */}
      <div className="w-1/2 rounded-lg border border-border/60 bg-white dark:bg-slate-900 overflow-hidden">
        <div className="px-3 py-2 border-b border-border/60 bg-muted/30">
          <span className="text-xs font-medium text-muted-foreground">Architecture Diagram</span>
        </div>
        <div className="h-[calc(100%-2.5rem)]">
          <MermaidDiagram
            code={approach.mermaidCode}
            onElementClick={handleDiagramClick}
            highlightedElement={
              isHighlightedApproach && refinementTarget?.elementType === "diagram"
                ? refinementTarget.elementId
                : undefined
            }
          />
        </div>
      </div>

      {/* Task Table - Right Half */}
      <div className="w-1/2 rounded-lg border border-border/60 bg-white dark:bg-slate-900 overflow-hidden">
        <div className="px-3 py-2 border-b border-border/60 bg-muted/30">
          <span className="text-xs font-medium text-muted-foreground">Implementation Tasks</span>
        </div>
        <div className="h-[calc(100%-2.5rem)]">
          <TaskTable
            tasks={approach.tasks}
            onTaskClick={handleTaskClick}
            highlightedTask={
              isHighlightedApproach && refinementTarget?.elementType === "task"
                ? refinementTarget.elementId
                : undefined
            }
          />
        </div>
      </div>
    </div>
  );
}
