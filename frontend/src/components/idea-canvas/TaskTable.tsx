// frontend/src/components/idea-canvas/TaskTable.tsx

"use client";

import { useState, useCallback } from "react";
import { Button } from "@/components/ui/button";
import { ApproachTask } from "@/lib/types/idea-canvas";

interface TaskTableProps {
  tasks: ApproachTask[];
  onTaskClick?: (taskId: string) => void;
  highlightedTask?: string;
}

const complexityColors = {
  Low: "bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400",
  Medium: "bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-400",
  High: "bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400",
};

export function TaskTable({
  tasks,
  onTaskClick,
  highlightedTask,
}: TaskTableProps) {
  const [copied, setCopied] = useState(false);

  const handleCopy = useCallback(async () => {
    // Generate markdown table
    const header = "| Task | Description | Tech Stack | Complexity |";
    const separator = "|------|-------------|------------|------------|";
    const rows = tasks.map(
      (t) => `| ${t.name} | ${t.description} | ${t.techStack} | ${t.complexity} |`
    );
    const markdown = [header, separator, ...rows].join("\n");

    try {
      await navigator.clipboard.writeText(markdown);
      setCopied(true);
      setTimeout(() => setCopied(false), 1500);
    } catch {
      const textarea = document.createElement("textarea");
      textarea.value = markdown;
      document.body.appendChild(textarea);
      textarea.select();
      document.execCommand("copy");
      document.body.removeChild(textarea);
      setCopied(true);
      setTimeout(() => setCopied(false), 1500);
    }
  }, [tasks]);

  return (
    <div className="relative h-full flex flex-col">
      <div className="flex-1 overflow-auto">
        <table className="w-full text-sm">
          <thead className="sticky top-0 bg-muted/80 backdrop-blur-sm">
            <tr className="border-b">
              <th className="text-left p-3 font-medium">Task</th>
              <th className="text-left p-3 font-medium">Description</th>
              <th className="text-left p-3 font-medium">Tech Stack</th>
              <th className="text-left p-3 font-medium w-24">Complexity</th>
            </tr>
          </thead>
          <tbody>
            {tasks.map((task) => (
              <tr
                key={task.id}
                onClick={() => onTaskClick?.(task.id)}
                className={`border-b transition-colors ${
                  onTaskClick ? "cursor-pointer hover:bg-muted/50" : ""
                } ${highlightedTask === task.id ? "bg-blue-50 dark:bg-blue-900/20 ring-2 ring-blue-500 ring-inset" : ""}`}
              >
                <td className="p-3 font-medium">{task.name}</td>
                <td className="p-3 text-muted-foreground">{task.description}</td>
                <td className="p-3">
                  <code className="text-xs bg-muted px-1.5 py-0.5 rounded">
                    {task.techStack}
                  </code>
                </td>
                <td className="p-3">
                  <span
                    className={`text-xs px-2 py-1 rounded-full font-medium ${
                      complexityColors[task.complexity]
                    }`}
                  >
                    {task.complexity}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <div className="absolute bottom-3 right-3">
        <Button
          variant="outline"
          size="sm"
          onClick={handleCopy}
          className="h-8 text-xs bg-background/80 backdrop-blur-sm"
        >
          {copied ? (
            <>
              <svg className="w-3.5 h-3.5 mr-1.5 text-emerald-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
              </svg>
              Copied!
            </>
          ) : (
            <>
              <svg className="w-3.5 h-3.5 mr-1.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
              </svg>
              Copy Table
            </>
          )}
        </Button>
      </div>
    </div>
  );
}
