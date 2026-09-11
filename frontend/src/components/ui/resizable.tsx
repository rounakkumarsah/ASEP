"use client"

import { GripVertical } from "lucide-react"
import * as ResizablePrimitive from "react-resizable-panels"

import { cn } from "@/lib/utils"

// eslint-disable-next-line @typescript-eslint/no-explicit-any
const PanelGroupAny = (ResizablePrimitive as any).PanelGroup || (ResizablePrimitive as any).Group;
// eslint-disable-next-line @typescript-eslint/no-explicit-any
const PanelAny = (ResizablePrimitive as any).Panel;
// eslint-disable-next-line @typescript-eslint/no-explicit-any
const PanelResizeHandleAny = (ResizablePrimitive as any).PanelResizeHandle || (ResizablePrimitive as any).Separator;

const ResizablePanelGroup = ({
  className,
  ...props
// eslint-disable-next-line @typescript-eslint/no-explicit-any
}: any) => (
  <PanelGroupAny
    className={cn(
      "flex h-full w-full data-[panel-group-direction=vertical]:flex-col",
      className
    )}
    {...props}
  />
)

const ResizablePanel = PanelAny

const ResizableHandle = ({
  withHandle,
  className,
  ...props
// eslint-disable-next-line @typescript-eslint/no-explicit-any
}: any) => (
  <PanelResizeHandleAny
    className={cn(
      "relative flex w-px items-center justify-center bg-border after:absolute after:inset-y-0 after:left-1/2 after:w-1 after:-translate-x-1/2 focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring focus-visible:ring-offset-1 data-[panel-group-direction=vertical]:h-px data-[panel-group-direction=vertical]:w-full data-[panel-group-direction=vertical]:after:left-0 data-[panel-group-direction=vertical]:after:h-1 data-[panel-group-direction=vertical]:after:w-full data-[panel-group-direction=vertical]:after:-translate-y-1/2 data-[panel-group-direction=vertical]:after:translate-x-0 [&[data-panel-group-direction=vertical]>div]:rotate-90",
      className
    )}
    {...props}
  >
    {withHandle && (
      <div className="z-10 flex h-4 w-3 items-center justify-center rounded-sm border bg-border">
        <GripVertical className="h-2.5 w-2.5" />
      </div>
    )}
  </PanelResizeHandleAny>
)

export { ResizablePanelGroup, ResizablePanel, ResizableHandle }
