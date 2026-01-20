// frontend/src/components/mindmap/MindMapViewer.tsx

"use client";

import { useCallback, useMemo, useState, useRef, useEffect } from "react";
import {
  ReactFlow,
  Background,
  MiniMap,
  useNodesState,
  useEdgesState,
  useReactFlow,
  ReactFlowProvider,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";

import { MindMapNode } from "./MindMapNode";
import { MindMapToolbar } from "./MindMapToolbar";
import { MindMapTree } from "@/lib/types/mindmap";
import { treeToFlow, getAllNodeIds } from "@/lib/mindmap/treeToFlow";
import { exportToPng, exportToSvg, exportToJson } from "@/lib/mindmap/exportMindMap";
import { Button } from "@/components/ui/button";
import { FeedbackButtons } from "@/components/feedback/FeedbackButtons";

const nodeTypes = {
  mindMapNode: MindMapNode,
};

interface MindMapViewerInnerProps {
  tree: MindMapTree;
  onReset: () => void;
}

function MindMapViewerInner({ tree, onReset }: MindMapViewerInnerProps) {
  const reactFlowWrapper = useRef<HTMLDivElement>(null);
  const fullscreenContainerRef = useRef<HTMLDivElement>(null);
  const [expandedNodes, setExpandedNodes] = useState<Set<string>>(() => {
    // Start with all nodes expanded
    return new Set(getAllNodeIds(tree.nodes));
  });
  const [isExporting, setIsExporting] = useState(false);
  const [isFullScreen, setIsFullScreen] = useState(false);

  const { zoomIn, zoomOut, fitView } = useReactFlow();

  // Listen for fullscreen changes
  useEffect(() => {
    const handleFullscreenChange = () => {
      setIsFullScreen(!!document.fullscreenElement);
      // Fit view after fullscreen change with a small delay for layout to settle
      setTimeout(() => fitView({ padding: 0.2 }), 100);
    };

    document.addEventListener("fullscreenchange", handleFullscreenChange);
    return () => document.removeEventListener("fullscreenchange", handleFullscreenChange);
  }, [fitView]);

  const handleFullScreen = useCallback(async () => {
    if (!fullscreenContainerRef.current) return;

    try {
      if (!document.fullscreenElement) {
        await fullscreenContainerRef.current.requestFullscreen();
      } else {
        await document.exitFullscreen();
      }
    } catch (err) {
      console.error("Fullscreen error:", err);
    }
  }, []);

  const { nodes: initialNodes, edges: initialEdges } = useMemo(
    () => treeToFlow(tree.nodes, expandedNodes),
    [tree.nodes, expandedNodes]
  );

  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges);

  // Update nodes when expanded state changes
  useEffect(() => {
    const { nodes: newNodes, edges: newEdges } = treeToFlow(tree.nodes, expandedNodes);
    setNodes(newNodes);
    setEdges(newEdges);
  }, [expandedNodes, tree.nodes, setNodes, setEdges]);

  const handleToggleNode = useCallback((nodeId: string) => {
    setExpandedNodes((prev) => {
      const next = new Set(prev);
      if (next.has(nodeId)) {
        next.delete(nodeId);
      } else {
        next.add(nodeId);
      }
      return next;
    });
  }, []);

  // Add toggle handler to node data
  const nodesWithHandlers = useMemo(
    () =>
      nodes.map((node) => ({
        ...node,
        data: { ...node.data, onToggle: handleToggleNode },
      })),
    [nodes, handleToggleNode]
  );

  const handleExpandAll = useCallback(() => {
    setExpandedNodes(new Set(getAllNodeIds(tree.nodes)));
  }, [tree.nodes]);

  const handleCollapseAll = useCallback(() => {
    // Keep only root expanded
    setExpandedNodes(new Set([tree.nodes.id]));
  }, [tree.nodes.id]);

  const handleExport = useCallback(
    async (format: "png" | "svg" | "json") => {
      if (format === "json") {
        exportToJson(tree, tree.title);
        return;
      }

      // Get the entire React Flow container for better export
      const element = reactFlowWrapper.current?.querySelector(
        ".react-flow"
      ) as HTMLElement;
      if (!element) return;

      setIsExporting(true);
      try {
        // Temporarily expand all for export
        const prevExpanded = new Set(expandedNodes);
        setExpandedNodes(new Set(getAllNodeIds(tree.nodes)));

        // Wait for re-render and fit view
        await new Promise((resolve) => setTimeout(resolve, 200));
        fitView({ padding: 0.1 });
        await new Promise((resolve) => setTimeout(resolve, 100));

        if (format === "png") {
          await exportToPng(element, tree.title);
        } else {
          await exportToSvg(element, tree.title);
        }

        // Restore previous state
        setExpandedNodes(prevExpanded);
      } finally {
        setIsExporting(false);
      }
    },
    [tree, expandedNodes, fitView]
  );

  return (
    <div ref={fullscreenContainerRef} className={`relative flex flex-col h-full ${isFullScreen ? "bg-background" : ""}`}>
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b">
        <div>
          <h2 className="text-lg font-semibold">{tree.title}</h2>
          <p className="text-sm text-muted-foreground">
            Based on {tree.source_count} source{tree.source_count !== 1 ? "s" : ""}
          </p>
        </div>
        <FeedbackButtons
          contentType="mindmap"
          metadata={{ title: tree.title, mode: tree.mode, source_count: tree.source_count }}
        />
      </div>

      {/* Toolbar - positioned top-right to avoid blocking back button */}
      <div className="absolute top-20 right-4 z-10">
        <MindMapToolbar
          onZoomIn={() => zoomIn()}
          onZoomOut={() => zoomOut()}
          onFitView={() => fitView({ padding: 0.2 })}
          onFullScreen={handleFullScreen}
          onExpandAll={handleExpandAll}
          onCollapseAll={handleCollapseAll}
          onExport={handleExport}
          isExporting={isExporting}
          isFullScreen={isFullScreen}
        />
      </div>

      {/* React Flow */}
      <div ref={reactFlowWrapper} className="flex-1">
        <ReactFlow
          nodes={nodesWithHandlers}
          edges={edges}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          nodeTypes={nodeTypes}
          fitView
          minZoom={0.1}
          maxZoom={2}
          panOnScroll
          selectionOnDrag={false}
          nodesDraggable={false}
          nodesConnectable={false}
          elementsSelectable={false}
        >
          <Background color="#334155" gap={20} />
          <MiniMap
            nodeColor={(node) => (node.data as { colors?: { bg?: string } })?.colors?.bg || "#06b6d4"}
            maskColor="rgba(15, 23, 42, 0.8)"
          />
        </ReactFlow>
      </div>

      {/* Footer - hide in fullscreen */}
      {!isFullScreen && (
        <div className="p-4 border-t flex justify-center">
          <Button variant="outline" onClick={onReset}>
            Generate Another
          </Button>
        </div>
      )}
    </div>
  );
}

interface MindMapViewerProps {
  tree: MindMapTree | null;
  onReset: () => void;
}

export function MindMapViewer({ tree, onReset }: MindMapViewerProps) {
  if (!tree) {
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
          Ready to Generate
        </h3>
        <p className="text-sm text-muted-foreground/70 max-w-xs">
          Fill in the form and click &quot;Generate Mind Map&quot; to visualize your content
        </p>
      </div>
    );
  }

  return (
    <ReactFlowProvider>
      <MindMapViewerInner tree={tree} onReset={onReset} />
    </ReactFlowProvider>
  );
}
