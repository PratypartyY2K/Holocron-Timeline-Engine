"use client";

import {
  BaseEdge,
  getBezierPath,
  type Edge,
  type EdgeProps,
  type EdgeTypes,
} from "@xyflow/react";

type CausalEdgeData = {
  note?: string;
  onHoverNoteChange?: (note: string | null) => void;
};

type CausalEdgeRecord = Edge<CausalEdgeData, "causal">;

export function CausalEdge({
  id,
  sourceX,
  sourceY,
  targetX,
  targetY,
  sourcePosition,
  targetPosition,
  markerEnd,
  style,
  data,
}: EdgeProps<CausalEdgeRecord>) {
  const [path] = getBezierPath({
    sourceX,
    sourceY,
    sourcePosition,
    targetX,
    targetY,
    targetPosition,
  });

  return (
    <>
      <BaseEdge id={id} path={path} markerEnd={markerEnd} style={style} />
      <path
        d={path}
        fill="none"
        stroke="transparent"
        strokeWidth={24}
        pointerEvents="stroke"
        onMouseEnter={() => data?.onHoverNoteChange?.(data.note ?? null)}
        onMouseLeave={() => data?.onHoverNoteChange?.(null)}
      />
    </>
  );
}

export const CAUSAL_EDGE_TYPES: EdgeTypes = {
  causal: CausalEdge,
};
