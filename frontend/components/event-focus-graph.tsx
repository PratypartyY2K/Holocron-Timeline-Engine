"use client";

import type { Route } from "next";
import { useRouter } from "next/navigation";
import { useCallback, useMemo, useState, type ReactNode } from "react";
import ReactFlow, {
  Background,
  Controls,
  MarkerType,
  MiniMap,
  type Edge,
  type EdgeTypes,
  type Node,
  type NodeMouseHandler,
} from "reactflow";
import "reactflow/dist/style.css";

import { CausalEdge } from "./causal-edge";
import type { CausalGraphResponse, EventImpactResponse, EventRecord } from "../lib/holocron-api";

type EventFocusGraphProps = {
  graph: CausalGraphResponse;
  impact?: EventImpactResponse | null;
  impactLoading?: boolean;
  simulateDisabled?: boolean;
};

type GraphNodeData = {
  label: ReactNode;
  slug: string;
  tone: "dependency" | "focus" | "consequence";
  status: "normal" | "deactivated" | "broken";
};

const edgeTypes: EdgeTypes = {
  causal: CausalEdge,
};

const EDGE_TYPES = Object.freeze(edgeTypes);

const DEFAULT_EDGE_OPTIONS = Object.freeze({
  style: {
    stroke: "rgba(233, 180, 76, 0.55)",
    strokeWidth: 1.6,
  },
});

function formatChronology(year: number): string {
  if (year < 0) {
    return `${Math.abs(year)} BBY`;
  }
  if (year > 0) {
    return `${year} ABY`;
  }
  return "0 ABY";
}

function eventChronology(event: EventRecord): string {
  if (event.end_year === null || event.end_year === event.start_year) {
    return formatChronology(event.start_year);
  }
  return `${formatChronology(event.start_year)} to ${formatChronology(event.end_year)}`;
}

function buildLabel(event: EventRecord): ReactNode {
  return (
    <div className="graph-node">
      <div className="graph-node-chronology">{eventChronology(event)}</div>
      <div className="graph-node-title">{event.title}</div>
      <div className="graph-node-era">{event.era ?? "Unclassified era"}</div>
    </div>
  );
}

function buildGraph(
  graph: CausalGraphResponse,
  impact: EventImpactResponse | null | undefined,
  simulateDisabled: boolean,
): { nodes: Node<GraphNodeData>[]; edges: Edge[] } {
  const impactedNodeIds = new Set(impact?.impacted_events.map((item) => item.id) ?? []);
  const brokenEdgeIds = new Set(impact?.broken_edges.map((item) => item.id) ?? []);
  const incoming = new Map<string, string[]>();
  const outgoing = new Map<string, string[]>();
  for (const edge of graph.edges) {
    const nextOutgoing = outgoing.get(edge.source_id) ?? [];
    nextOutgoing.push(edge.target_id);
    outgoing.set(edge.source_id, nextOutgoing);

    const nextIncoming = incoming.get(edge.target_id) ?? [];
    nextIncoming.push(edge.source_id);
    incoming.set(edge.target_id, nextIncoming);
  }

  const dependencyDistance = new Map<string, number>([[graph.focus_event_id, 0]]);
  const dependencyQueue: string[] = [graph.focus_event_id];
  while (dependencyQueue.length > 0) {
    const current = dependencyQueue.shift();
    if (current === undefined) {
      break;
    }
    const distance = dependencyDistance.get(current) ?? 0;
    for (const parent of incoming.get(current) ?? []) {
      if (!dependencyDistance.has(parent)) {
        dependencyDistance.set(parent, distance - 1);
        dependencyQueue.push(parent);
      }
    }
  }

  const consequenceDistance = new Map<string, number>([[graph.focus_event_id, 0]]);
  const consequenceQueue: string[] = [graph.focus_event_id];
  while (consequenceQueue.length > 0) {
    const current = consequenceQueue.shift();
    if (current === undefined) {
      break;
    }
    const distance = consequenceDistance.get(current) ?? 0;
    for (const child of outgoing.get(current) ?? []) {
      if (!consequenceDistance.has(child)) {
        consequenceDistance.set(child, distance + 1);
        consequenceQueue.push(child);
      }
    }
  }

  const columns = new Map<number, EventRecord[]>();
  for (const node of graph.nodes) {
    const incomingDistance = dependencyDistance.get(node.id);
    const outgoingDistance = consequenceDistance.get(node.id);
    const column =
      node.id === graph.focus_event_id
        ? 0
        : incomingDistance !== undefined && incomingDistance < 0
          ? incomingDistance
          : outgoingDistance ?? 0;
    const bucket = columns.get(column) ?? [];
    bucket.push(node);
    columns.set(column, bucket);
  }

  const sortedColumns = Array.from(columns.entries()).sort((left, right) => left[0] - right[0]);
  const reactFlowNodes: Node<GraphNodeData>[] = [];
  for (const [columnIndex, events] of sortedColumns) {
    events.sort((left, right) => {
      if (left.start_year !== right.start_year) {
        return left.start_year - right.start_year;
      }
      return left.title.localeCompare(right.title);
    });

    events.forEach((event, rowIndex) => {
      const tone: GraphNodeData["tone"] =
        event.id === graph.focus_event_id
          ? "focus"
          : columnIndex < 0
            ? "dependency"
            : "consequence";
      const status: GraphNodeData["status"] =
        simulateDisabled && event.id === graph.focus_event_id
          ? "deactivated"
          : simulateDisabled && impactedNodeIds.has(event.id)
            ? "broken"
            : "normal";

      reactFlowNodes.push({
        id: event.id,
        type: "default",
        position: { x: 380 + columnIndex * 320, y: 40 + rowIndex * 128 },
        className: `graph-node-shell graph-node-shell-${status}`,
        data: {
          label: buildLabel(event),
          slug: event.slug,
          tone,
          status,
        },
        draggable: false,
      });
    });
  }

  const reactFlowEdges: Edge[] = graph.edges.map((edge) => ({
    id: edge.id,
    source: edge.source_id,
    target: edge.target_id,
    type: "causal",
    markerEnd: { type: MarkerType.ArrowClosed },
    animated: false,
    style:
      simulateDisabled && brokenEdgeIds.has(edge.id)
        ? {
            stroke: "rgba(255, 114, 122, 0.92)",
            strokeWidth: 2.4,
          }
        : undefined,
    data: {
      note: edge.note ?? "",
    },
  }));

  return { nodes: reactFlowNodes, edges: reactFlowEdges };
}

function nodeColor(tone: GraphNodeData["tone"], status: GraphNodeData["status"]): string {
  if (status === "broken") {
    return "#ff727a";
  }
  if (status === "deactivated") {
    return "#8893a3";
  }
  if (tone === "focus") {
    return "#e9b44c";
  }
  if (tone === "dependency") {
    return "#70c1b3";
  }
  return "#ff9ba7";
}

export function EventFocusGraph({
  graph,
  impact,
  impactLoading = false,
  simulateDisabled = false,
}: EventFocusGraphProps) {
  const router = useRouter();
  const [hoveredNote, setHoveredNote] = useState<string | null>(null);
  const handleHoverNoteChange = useCallback((note: string | null) => {
    setHoveredNote((current) => (current === note ? current : note));
  }, []);
  const handleNodeClick = useCallback<NodeMouseHandler>(
    (_, node) => {
      const slug = (node.data as GraphNodeData).slug;
      router.push(`/events/${slug}` as Route);
    },
    [router],
  );

  const reactFlowGraph = useMemo(
    () => buildGraph(graph, impact, simulateDisabled),
    [graph, impact, simulateDisabled],
  );

  const edgesWithHoverData: Edge[] = useMemo(
    () =>
      reactFlowGraph.edges.map((edge) => ({
        ...edge,
        data: {
          ...(edge.data as Record<string, unknown> | undefined),
          onHoverNoteChange: handleHoverNoteChange,
        },
      })),
    [handleHoverNoteChange, reactFlowGraph.edges],
  );

  return (
    <div className="graph-shell">
      <div className="graph-header">
        <div>
          <p className="section-kicker">Graph View</p>
          <h2>Focused causal map</h2>
        </div>
        <p className="timeline-caption">
          Visualizing actual <code>CAUSES</code> edges within depth {graph.depth}. Nodes are laid
          out relative to the focus event rather than collapsed into a star.
          {simulateDisabled
            ? impactLoading
              ? " Sandbox impact is loading."
              : " Broken downstream nodes and links are highlighted in the graph."
            : ""}
        </p>
      </div>

      <div className="graph-note-panel" aria-live="polite">
        <span className="graph-note-label">Edge note</span>
        <p className="graph-note-copy">
          {hoveredNote ?? "Hover over a causal edge to inspect its relationship note."}
        </p>
      </div>

      <div className="graph-canvas">
        <ReactFlow
          nodes={reactFlowGraph.nodes}
          edges={edgesWithHoverData}
          fitView
          fitViewOptions={{ padding: 0.2 }}
          proOptions={{ hideAttribution: true }}
          nodesDraggable={false}
          nodesConnectable={false}
          elementsSelectable
          edgeTypes={EDGE_TYPES}
          defaultEdgeOptions={DEFAULT_EDGE_OPTIONS}
          nodeOrigin={[0, 0]}
          onNodeClick={handleNodeClick}
        >
          <MiniMap
            pannable
            zoomable
            nodeColor={(node) =>
              nodeColor(
                (node.data as GraphNodeData).tone,
                (node.data as GraphNodeData).status,
              )
            }
            maskColor="rgba(5, 11, 18, 0.6)"
          />
          <Controls showInteractive={false} />
          <Background color="rgba(233, 180, 76, 0.12)" gap={24} />
        </ReactFlow>
      </div>

      <div className="graph-legend">
        <span><i className="legend-dot legend-dependency" /> Dependencies</span>
        <span><i className="legend-dot legend-focus" /> Focus event</span>
        <span><i className="legend-dot legend-consequence" /> Consequences</span>
        {simulateDisabled ? <span><i className="legend-dot legend-broken" /> Broken path</span> : null}
      </div>
    </div>
  );
}
