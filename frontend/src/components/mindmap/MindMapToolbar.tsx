// frontend/src/components/mindmap/MindMapToolbar.tsx

"use client";

import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

interface MindMapToolbarProps {
  onZoomIn: () => void;
  onZoomOut: () => void;
  onFitView: () => void;
  onFullScreen: () => void;
  onExpandAll: () => void;
  onCollapseAll: () => void;
  onExport: (format: "png" | "svg" | "json") => void;
  isExporting?: boolean;
  isFullScreen?: boolean;
}

export function MindMapToolbar({
  onZoomIn,
  onZoomOut,
  onFitView,
  onFullScreen,
  onExpandAll,
  onCollapseAll,
  onExport,
  isExporting = false,
  isFullScreen = false,
}: MindMapToolbarProps) {
  return (
    <div className="flex items-center gap-2 p-2 bg-card/80 backdrop-blur rounded-lg border shadow-sm">
      {/* Zoom controls */}
      <div className="flex items-center gap-1">
        <Button variant="ghost" size="sm" onClick={onZoomIn} title="Zoom in">
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0zM10 7v3m0 0v3m0-3h3m-3 0H7" />
          </svg>
        </Button>
        <Button variant="ghost" size="sm" onClick={onZoomOut} title="Zoom out">
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0zM13 10H7" />
          </svg>
        </Button>
        <Button variant="ghost" size="sm" onClick={onFitView} title="Fit view">
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 8V4m0 0h4M4 4l5 5m11-1V4m0 0h-4m4 0l-5 5M4 16v4m0 0h4m-4 0l5-5m11 5l-5-5m5 5v-4m0 4h-4" />
          </svg>
        </Button>
        <Button variant="ghost" size="sm" onClick={onFullScreen} title={isFullScreen ? "Exit fullscreen" : "Fullscreen"}>
          {isFullScreen ? (
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 9L4 4m0 0v4m0-4h4m6 0l5-5m0 0v4m0-4h-4m-6 10l-5 5m0 0v-4m0 4h4m6 0l5 5m0 0v-4m0 4h-4" />
            </svg>
          ) : (
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 8V4m0 0h4M4 4l5 5m11-1V4m0 0h-4m4 0l-5 5M4 16v4m0 0h4m-4 0l5-5m11 5l-5-5m5 5v-4m0 4h-4" />
            </svg>
          )}
        </Button>
      </div>

      <div className="w-px h-6 bg-border" />

      {/* Expand/Collapse */}
      <div className="flex items-center gap-1">
        <Button variant="ghost" size="sm" onClick={onExpandAll} title="Expand all">
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 8h16M4 16h16" />
          </svg>
        </Button>
        <Button variant="ghost" size="sm" onClick={onCollapseAll} title="Collapse all">
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20 12H4" />
          </svg>
        </Button>
      </div>

      <div className="w-px h-6 bg-border" />

      {/* Export */}
      <Select
        onValueChange={(value) => onExport(value as "png" | "svg" | "json")}
        disabled={isExporting}
      >
        <SelectTrigger className="w-[120px] h-8">
          <SelectValue placeholder="Export" />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="png">Export PNG</SelectItem>
          <SelectItem value="svg">Export SVG</SelectItem>
          <SelectItem value="json">Export JSON</SelectItem>
        </SelectContent>
      </Select>
    </div>
  );
}
