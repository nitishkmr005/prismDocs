// frontend/src/components/idea-canvas/IdeaCanvas.tsx

"use client";

import { useMemo, useCallback, useEffect, useRef } from "react";
import {
  ReactFlow,
  Background,
  MiniMap,
  useNodesState,
  useEdgesState,
  useReactFlow,
  ReactFlowProvider,
  Node,
  Edge,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";

import { Button } from "@/components/ui/button";
import { CanvasNodeMemo } from "./CanvasNode";
import { QuestionCard } from "./QuestionCard";
import {
  CanvasState,
  CanvasQuestion,
  CanvasNode as CanvasNodeType,
} from "@/lib/types/idea-canvas";

const nodeTypes = {
  canvasNode: CanvasNodeMemo,
};

interface IdeaCanvasInnerProps {
  canvas: CanvasState;
  currentQuestion: CanvasQuestion | null;
  progressMessage: string | null;
  isAnswering: boolean;
  onAnswer: (answer: string | string[]) => void;
  onReset: () => void;
  onGenerateReport?: () => void;
  isSuggestComplete?: boolean;
  hideQuestionCard?: boolean;
}

// Convert canvas tree to ReactFlow nodes and edges with horizontal tree layout
// Options now branch from QUESTION nodes (not ANSWER nodes), with selected option highlighted green
function canvasToFlow(
  rootNode: CanvasNodeType,
  activeQuestionId?: string,
): { nodes: Node[]; edges: Edge[] } {
  const nodes: Node[] = [];
  const edges: Edge[] = [];
  
  // Tree layout configuration (left to right)
  const NODE_WIDTH = 300;  // Match CSS max-width for proper edge lengths
  const NODE_HEIGHT = 80;
  const OPTION_NODE_HEIGHT = 50; // Smaller height for option nodes
  const HORIZONTAL_SPACING = 100; // Space between parent and children (edge length)
  const VERTICAL_SPACING = 30;   // Space between siblings
  const OPTION_SPACING = 24;     // Extra breathing room between options
  const SELECTED_OPTION_GAP = 12; // Extra separation after the selected option

  // Helper to find answer child with options from a question node
  const getAnswerWithOptions = (node: CanvasNodeType) => {
    if (node.type !== "question") return null;
    const answerChild = node.children.find(c => c.type === "answer");
    if (answerChild && answerChild.options && answerChild.options.length > 0) {
      return answerChild;
    }
    return null;
  };

  const getOptionsHeight = (
    options: { id: string }[],
    selectedId?: string,
  ) => {
    const baseHeight =
      options.length * OPTION_NODE_HEIGHT +
      (options.length - 1) * OPTION_SPACING;
    if (!selectedId) return baseHeight;
    const selectedIndex = options.findIndex((option) => option.id === selectedId);
    if (selectedIndex === -1 || selectedIndex === options.length - 1) {
      return baseHeight;
    }
    return baseHeight + SELECTED_OPTION_GAP;
  };

  // Calculate subtree height - now considering options branching from question nodes
  const getSubtreeHeight = (node: CanvasNodeType): number => {
    // For question nodes, check if their answer child has options
    const answerWithOptions = getAnswerWithOptions(node);
    if (answerWithOptions) {
      // Options height (they branch from question)
      const optionsHeight = getOptionsHeight(
        answerWithOptions.options!,
        answerWithOptions.selected_option_id,
      );
      
      // The answer's children will branch from the selected option
      let childrenHeight = 0;
      if (answerWithOptions.children.length > 0) {
        answerWithOptions.children.forEach(child => {
          childrenHeight += getSubtreeHeight(child);
        });
        childrenHeight += (answerWithOptions.children.length - 1) * VERTICAL_SPACING;
      }
      
      return Math.max(NODE_HEIGHT, optionsHeight, childrenHeight);
    }

    // For answer nodes with options (shouldn't happen in new flow, but keep for safety)
    if (node.type === "answer" && node.options && node.options.length > 0) {
      const optionsHeight = getOptionsHeight(
        node.options,
        node.selected_option_id,
      );
      
      if (node.children.length === 0) {
        return Math.max(NODE_HEIGHT, optionsHeight);
      }
      
      let childrenHeight = 0;
      node.children.forEach(child => {
        childrenHeight += getSubtreeHeight(child);
      });
      childrenHeight += (node.children.length - 1) * VERTICAL_SPACING;
      
      return Math.max(NODE_HEIGHT, optionsHeight, childrenHeight);
    }

    if (node.children.length === 0) {
      return NODE_HEIGHT;
    }
    
    let totalHeight = 0;
    node.children.forEach((child) => {
      totalHeight += getSubtreeHeight(child);
    });
    totalHeight += (node.children.length - 1) * VERTICAL_SPACING;
    
    return Math.max(NODE_HEIGHT, totalHeight);
  };

  const processNode = (
    node: CanvasNodeType,
    x: number,
    y: number,
    depth: number,
  ) => {
    const isActive = node.id === activeQuestionId;

    // Check if this is a question node with an answer child that has options
    const answerWithOptions = getAnswerWithOptions(node);

    // Create the current node
    nodes.push({
      id: node.id,
      type: "canvasNode",
      position: { x, y },
      data: {
        label: node.label,
        description: node.description,
        nodeType: node.type,
        isActive,
      },
    });

    // If this is a QUESTION with an answer that has options -> options branch from question
    if (answerWithOptions) {
      // Create option nodes branching from this question (not the answer)
      const optionX = x + NODE_WIDTH + HORIZONTAL_SPACING;
      const totalOptionsHeight = getOptionsHeight(
        answerWithOptions.options!,
        answerWithOptions.selected_option_id,
      );
      let optionY = y + (NODE_HEIGHT - totalOptionsHeight) / 2;

      answerWithOptions.options!.forEach((option, index) => {
        const optionNodeId = `${node.id}_opt_${option.id}`;
        const isSelectedOption = option.id === answerWithOptions.selected_option_id;
        const extraSelectedGap =
          isSelectedOption && index < answerWithOptions.options!.length - 1
            ? SELECTED_OPTION_GAP
            : 0;

        nodes.push({
          id: optionNodeId,
          type: "canvasNode",
          position: { x: optionX, y: optionY },
          data: {
            label: option.label,
            description: option.description,
            nodeType: "option" as const,
            isSelected: isSelectedOption,
          },
        });

        // Edge from question to option
        edges.push({
          id: `${node.id}-${optionNodeId}`,
          source: node.id,
          target: optionNodeId,
          type: "smoothstep",
          style: { 
            stroke: isSelectedOption ? "#10b981" : "#64748b", 
            strokeWidth: isSelectedOption ? 3 : 2,
          },
        });

        // If this is the selected option, connect answer's children (next questions) to it
        if (isSelectedOption && answerWithOptions.children.length > 0) {
          const childX = optionX + NODE_WIDTH + HORIZONTAL_SPACING;
          const childHeights = answerWithOptions.children.map(child => getSubtreeHeight(child));
          const totalChildrenHeight = childHeights.reduce((sum, h) => sum + h, 0) + 
            (answerWithOptions.children.length - 1) * VERTICAL_SPACING;
          let currentChildY = optionY + (OPTION_NODE_HEIGHT - totalChildrenHeight) / 2;

          answerWithOptions.children.forEach((child, index) => {
            const childHeight = childHeights[index];
            const childCenterY = currentChildY + (childHeight - NODE_HEIGHT) / 2;

            edges.push({
              id: `${optionNodeId}-${child.id}`,
              source: optionNodeId,
              target: child.id,
              type: "smoothstep",
              animated: child.id === activeQuestionId,
              style: { 
                stroke: "#475569", 
                strokeWidth: 3 
              },
            });

            processNode(child, childX, childCenterY, depth + 1);
            currentChildY += childHeight + VERTICAL_SPACING;
          });
        }

        optionY += OPTION_NODE_HEIGHT + OPTION_SPACING + extraSelectedGap;
      });
      
      // Don't process children normally - we already handled answer's children above
      return;
    }

    // Process children with proper horizontal tree layout (for nodes without options from question)
    const childCount = node.children.length;
    if (childCount > 0) {
      // Filter out answer nodes that have options (they're represented by options branching from question)
      const visibleChildren = node.children.filter(child => {
        // Skip answer nodes that have options - their content is shown as options from the question
        if (child.type === "answer" && child.options && child.options.length > 0) {
          return false;
        }
        return true;
      });

      if (visibleChildren.length === 0) return;

      const childHeights = visibleChildren.map(child => getSubtreeHeight(child));
      const totalChildrenHeight = childHeights.reduce((sum, h) => sum + h, 0) + 
        (visibleChildren.length - 1) * VERTICAL_SPACING;
      
      const childX = x + NODE_WIDTH + HORIZONTAL_SPACING;
      let currentY = y + (NODE_HEIGHT - totalChildrenHeight) / 2;

      visibleChildren.forEach((child, index) => {
        const childHeight = childHeights[index];
        const childCenterY = currentY + (childHeight - NODE_HEIGHT) / 2;

        edges.push({
          id: `${node.id}-${child.id}`,
          source: node.id,
          target: child.id,
          type: "smoothstep",
          animated: child.id === activeQuestionId,
          style: { 
            stroke: child.type === "answer" ? "#10b981" : "#475569", 
            strokeWidth: 3 
          },
        });

        processNode(child, childX, childCenterY, depth + 1);
        currentY += childHeight + VERTICAL_SPACING;
      });
    }
  };

  // Calculate initial Y position to center the tree
  const treeHeight = getSubtreeHeight(rootNode);
  const startY = Math.max(50, 300 - treeHeight / 2);
  
  processNode(rootNode, 50, startY, 0);

  return { nodes, edges };
}


function IdeaCanvasInner({
  canvas,
  currentQuestion,
  progressMessage,
  isAnswering,
  onAnswer,
  onReset,
  onGenerateReport,
  isSuggestComplete = false,
  hideQuestionCard = false,
}: IdeaCanvasInnerProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const { fitView } = useReactFlow();

  const { nodes: initialNodes, edges: initialEdges } = useMemo(
    () => canvasToFlow(canvas.nodes, currentQuestion?.id),
    [canvas.nodes, currentQuestion?.id],
  );

  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges);

  // Update nodes when canvas changes
  useEffect(() => {
    const { nodes: newNodes, edges: newEdges } = canvasToFlow(
      canvas.nodes,
      currentQuestion?.id,
    );
    setNodes(newNodes);
    setEdges(newEdges);

    // Fit view after update with delay
    setTimeout(() => fitView({ padding: 0.2, duration: 300 }), 100);
  }, [canvas.nodes, currentQuestion?.id, setNodes, setEdges, fitView]);

  const handleSkip = useCallback(() => {
    onAnswer("Skipped");
  }, [onAnswer]);

  return (
    <div ref={containerRef} className="relative w-full h-full min-h-[500px]">
      {/* ReactFlow Canvas */}
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        nodeTypes={nodeTypes}
        fitView
        minZoom={0.2}
        maxZoom={1.5}
        panOnScroll
        selectionOnDrag={false}
        nodesDraggable={false}
        nodesConnectable={false}
        elementsSelectable={false}
      >
        <Background color="#334155" gap={20} />
        <MiniMap
          nodeColor={(node) => {
            const nodeType = (node.data as { nodeType?: string })?.nodeType;
            const isSelected = (node.data as { isSelected?: boolean })?.isSelected;
            switch (nodeType) {
              case "root":
                return "#6366f1";
              case "question":
                return "#64748b";
              case "answer":
                return "#10b981";
              case "approach":
                return "#f59e0b";
              case "option":
                return isSelected ? "#10b981" : "#94a3b8";
              default:
                return "#64748b";
            }
          }}
          maskColor="rgba(15, 23, 42, 0.8)"
        />
      </ReactFlow>

      {/* Progress Message */}
      {progressMessage && !currentQuestion && !isSuggestComplete && (
        <div className="absolute bottom-8 left-1/2 -translate-x-1/2 z-10">
          <div className="bg-card border rounded-lg px-6 py-3 shadow-lg flex items-center gap-3">
            <div className="w-5 h-5 border-2 border-primary border-t-transparent rounded-full animate-spin" />
            <span className="text-sm font-medium">{progressMessage}</span>
          </div>
        </div>
      )}

      {/* Question Card - Floating (only show if hideQuestionCard is false) */}
      {currentQuestion && !isSuggestComplete && !hideQuestionCard && (
        <div className="absolute bottom-8 right-8 z-10">
          <QuestionCard
            question={currentQuestion}
            onAnswer={onAnswer}
            onSkip={currentQuestion.allow_skip ? handleSkip : undefined}
            isAnswering={isAnswering}
          />
        </div>
      )}

      {/* Completion Suggestion (only show if hideQuestionCard is false) */}
      {isSuggestComplete && !hideQuestionCard && (
        <div className="absolute bottom-8 left-1/2 -translate-x-1/2 z-10">
          <div className="bg-card border rounded-lg p-6 shadow-lg max-w-md text-center">
            <div className="w-12 h-12 bg-primary/10 rounded-full flex items-center justify-center mx-auto mb-4">
              <svg
                className="w-6 h-6 text-primary"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
                />
              </svg>
            </div>
            <h3 className="font-semibold text-lg mb-2">
              Ready to generate your spec?
            </h3>
            <p className="text-sm text-muted-foreground mb-4">
              {progressMessage ||
                "We've explored the key areas of your idea. Generate your implementation spec now or continue exploring."}
            </p>
            <div className="flex gap-3 justify-center">
              <Button variant="outline" onClick={() => onAnswer("continue")}>
                Keep Exploring
              </Button>
              {onGenerateReport && (
                <Button onClick={onGenerateReport}>Generate Report</Button>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Header with stats and reset (only show if hideQuestionCard is false) */}
      {!hideQuestionCard && (
        <div className="absolute top-4 left-4 z-10 flex items-center gap-4">
          <div className="bg-card/90 backdrop-blur border rounded-lg px-4 py-2 shadow-sm">
            <div className="text-xs text-muted-foreground">Questions asked</div>
            <div className="font-semibold">{canvas.question_count}</div>
          </div>
          <Button variant="outline" size="sm" onClick={onReset}>
            Start Over
          </Button>
        </div>
      )}
    </div>
  );
}

interface IdeaCanvasProps {
  canvas: CanvasState | null;
  currentQuestion: CanvasQuestion | null;
  progressMessage: string | null;
  isAnswering: boolean;
  onAnswer: (answer: string | string[]) => void;
  onReset: () => void;
  onGenerateReport?: () => void;
  isSuggestComplete?: boolean;
  hideQuestionCard?: boolean;
}

export function IdeaCanvas({
  canvas,
  currentQuestion,
  progressMessage,
  isAnswering,
  onAnswer,
  onReset,
  onGenerateReport,
  isSuggestComplete = false,
  hideQuestionCard = false,
}: IdeaCanvasProps) {
  if (!canvas) {
    return (
      <div className="flex flex-col items-center justify-center h-full min-h-[400px] text-center p-8 rounded-xl border border-dashed border-border bg-muted/20">
        <div className="w-16 h-16 rounded-full bg-muted/50 flex items-center justify-center mb-4">
          <svg
            className="w-8 h-8 text-muted-foreground"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={1.5}
              d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"
            />
          </svg>
        </div>
        <h3 className="text-lg font-medium text-muted-foreground mb-2">
          Ready to Explore
        </h3>
        <p className="text-sm text-muted-foreground/70 max-w-xs">
          Fill in the form and click &quot;Start Exploring&quot; to begin your
          idea canvas
        </p>
      </div>
    );
  }

  return (
    <ReactFlowProvider>
      <IdeaCanvasInner
        canvas={canvas}
        currentQuestion={currentQuestion}
        progressMessage={progressMessage}
        isAnswering={isAnswering}
        onAnswer={onAnswer}
        onReset={onReset}
        onGenerateReport={onGenerateReport}
        isSuggestComplete={isSuggestComplete}
        hideQuestionCard={hideQuestionCard}
      />
    </ReactFlowProvider>
  );
}
