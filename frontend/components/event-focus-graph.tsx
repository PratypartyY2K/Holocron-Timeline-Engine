"use client";

import type { Route } from "next";
import dagre from "@dagrejs/dagre";
import { useRouter } from "next/navigation";
import { useCallback, useMemo, useState, type ReactNode } from "react";
import ReactFlow, {
  Background,
  Controls,
  MarkerType,
  MiniMap,
  Position,
  type Edge,
  type EdgeTypes,
  type Node,
  type NodeMouseHandler,
} from "reactflow";
import "reactflow/dist/style.css";

import { CausalEdge } from "./causal-edge";
import type {
  CausalGraphResponse,
  EventRecord,
  TimelineBreakSimulationNodeRecord,
  TimelineBreakSimulationResponse,
} from "../lib/holocron-api";

type EventFocusGraphProps = {
  graph: CausalGraphResponse;
  simulation?: TimelineBreakSimulationResponse | null;
  simulationLoading?: boolean;
  simulateEnabled?: boolean;
};

type GraphNodeData = {
  label: ReactNode;
  slug: string;
  tone: "dependency" | "focus" | "consequence";
  status: "normal" | "deactivated" | "broken" | "invalidated" | "unresolved";
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

const NODE_WIDTH = 240;
const NODE_HEIGHT = 104;
const CHRONOLOGY_COLUMN_GAP = 320;
const LAYOUT_MARGIN_X = 80;
const LAYOUT_MARGIN_Y = 60;

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

function toRenderedNodeId(nodeId: string, mode: "canonical" | "simulation"): string {
  return mode === "simulation" ? `what-if:${nodeId}` : nodeId;
}

function buildCanonicalGraph(
  graph: CausalGraphResponse,
  simulateEnabled: boolean,
): { nodes: Node<GraphNodeData>[]; edges: Edge[] } {
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

  const reactFlowEdges: Edge[] = graph.edges.map((edge) => ({
    id: edge.id,
    source: toRenderedNodeId(edge.source_id, "canonical"),
    target: toRenderedNodeId(edge.target_id, "canonical"),
    type: "causal",
    markerEnd: { type: MarkerType.ArrowClosed },
    animated: false,
    sourcePosition: Position.Right,
    targetPosition: Position.Left,
    data: {
      note: edge.note ?? "",
    },
  }));

  const sortedEvents = [...graph.nodes].sort((left, right) => {
    if (left.start_year !== right.start_year) {
      return left.start_year - right.start_year;
    }
    return left.title.localeCompare(right.title);
  });
  const chronologyYears = Array.from(
    new Set(sortedEvents.map((event) => event.start_year)),
  ).sort((left, right) => left - right);
  const chronologyColumnByYear = new Map(
    chronologyYears.map((year, index) => [year, index]),
  );

  const dagreGraph = new dagre.graphlib.Graph();
  dagreGraph.setDefaultEdgeLabel(() => ({}));
  dagreGraph.setGraph({
    rankdir: "LR",
    align: "UL",
    nodesep: 52,
    ranksep: 96,
    edgesep: 30,
    marginx: LAYOUT_MARGIN_X,
    marginy: LAYOUT_MARGIN_Y,
  });

  for (const event of sortedEvents) {
    dagreGraph.setNode(event.id, {
      width: NODE_WIDTH,
      height: NODE_HEIGHT,
    });
  }

  for (const edge of graph.edges) {
    dagreGraph.setEdge(edge.source_id, edge.target_id);
  }

  dagre.layout(dagreGraph);

  const reactFlowNodes: Node<GraphNodeData>[] = sortedEvents.map((event) => {
    const tone: GraphNodeData["tone"] =
      event.id === graph.focus_event_id
        ? "focus"
        : (dependencyDistance.get(event.id) ?? 0) < 0
          ? "dependency"
          : "consequence";
    const status: GraphNodeData["status"] = simulateEnabled ? "deactivated" : "normal";
    const layoutNode = dagreGraph.node(event.id);
    const chronologyColumn = chronologyColumnByYear.get(event.start_year) ?? 0;

    return {
      id: toRenderedNodeId(event.id, "canonical"),
      type: "default",
      position: {
        x: LAYOUT_MARGIN_X + chronologyColumn * CHRONOLOGY_COLUMN_GAP,
        y: layoutNode.y - NODE_HEIGHT / 2,
      },
      className: `graph-node-shell graph-node-shell-${status}`,
      sourcePosition: Position.Right,
      targetPosition: Position.Left,
      data: {
        label: buildLabel(event),
        slug: event.slug,
        tone,
        status,
      },
      draggable: false,
    };
  });

  return { nodes: reactFlowNodes, edges: reactFlowEdges };
}

function buildSimulationGraph(
  simulation: TimelineBreakSimulationResponse,
): { nodes: Node<GraphNodeData>[]; edges: Edge[] } {
  const nodeById = new Map(simulation.nodes.map((node) => [node.id, node]));
  const incoming = new Map<string, string[]>();
  const outgoing = new Map<string, string[]>();
  for (const edge of simulation.edges) {
    const nextOutgoing = outgoing.get(edge.source_id) ?? [];
    nextOutgoing.push(edge.target_id);
    outgoing.set(edge.source_id, nextOutgoing);

    const nextIncoming = incoming.get(edge.target_id) ?? [];
    nextIncoming.push(edge.source_id);
    incoming.set(edge.target_id, nextIncoming);
  }

  const dependencyDistance = new Map<string, number>([[simulation.broken_event_id, 0]]);
  const dependencyQueue: string[] = [simulation.broken_event_id];
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

  const consequenceDistance = new Map<string, number>([[simulation.broken_event_id, 0]]);
  const consequenceQueue: string[] = [simulation.broken_event_id];
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

  const sortedNodes = [...simulation.nodes].sort((left, right) => {
    if (left.topological_rank !== right.topological_rank) {
      return left.topological_rank - right.topological_rank;
    }
    if (left.start_year !== right.start_year) {
      return left.start_year - right.start_year;
    }
    return left.title.localeCompare(right.title);
  });
  const chronologyYears = Array.from(new Set(sortedNodes.map((event) => event.start_year))).sort(
    (left, right) => left - right,
  );
  const chronologyColumnByYear = new Map(chronologyYears.map((year, index) => [year, index]));

  const dagreGraph = new dagre.graphlib.Graph();
  dagreGraph.setDefaultEdgeLabel(() => ({}));
  dagreGraph.setGraph({
    rankdir: "LR",
    align: "UL",
    nodesep: 52,
    ranksep: 96,
    edgesep: 30,
    marginx: LAYOUT_MARGIN_X,
    marginy: LAYOUT_MARGIN_Y,
  });

  for (const node of sortedNodes) {
    dagreGraph.setNode(node.id, {
      width: NODE_WIDTH,
      height: NODE_HEIGHT,
    });
  }

  for (const edge of simulation.edges) {
    dagreGraph.setEdge(edge.source_id, edge.target_id);
  }

  dagre.layout(dagreGraph);

  const reactFlowNodes: Node<GraphNodeData>[] = sortedNodes.map((event) => {
    const tone: GraphNodeData["tone"] =
      event.id === simulation.broken_event_id
        ? "focus"
        : (dependencyDistance.get(event.id) ?? 0) < 0
          ? "dependency"
          : "consequence";
    const layoutNode = dagreGraph.node(event.id);
    const chronologyColumn = chronologyColumnByYear.get(event.start_year) ?? 0;

    return {
      id: toRenderedNodeId(event.id, "simulation"),
      type: "default",
      position: {
        x: LAYOUT_MARGIN_X + chronologyColumn * CHRONOLOGY_COLUMN_GAP,
        y: layoutNode.y - NODE_HEIGHT / 2,
      },
      className: `graph-node-shell graph-node-shell-${toVisualStatus(event.status)}`,
      sourcePosition: Position.Right,
      targetPosition: Position.Left,
      data: {
        label: buildSimulationLabel(event, nodeById),
        slug: event.slug,
        tone,
        status: toVisualStatus(event.status),
      },
      draggable: false,
    };
  });

  const reactFlowEdges: Edge[] = simulation.edges.map((edge) => ({
    id: `what-if:${edge.id}`,
    source: toRenderedNodeId(edge.source_id, "simulation"),
    target: toRenderedNodeId(edge.target_id, "simulation"),
    type: "causal",
    markerEnd: { type: MarkerType.ArrowClosed },
    animated: false,
    sourcePosition: Position.Right,
    targetPosition: Position.Left,
    style:
      nodeById.get(edge.target_id)?.status === "invalidated"
        ? {
            stroke: "rgba(255, 114, 122, 0.92)",
            strokeWidth: 2.4,
          }
        : nodeById.get(edge.target_id)?.status === "unresolved"
          ? {
              stroke: "rgba(136, 147, 163, 0.92)",
              strokeWidth: 2,
              strokeDasharray: "6 4",
            }
          : undefined,
    data: {
      note: edge.note ?? "",
    },
  }));

  return { nodes: reactFlowNodes, edges: reactFlowEdges };
}

function buildSimulationLabel(
  event: TimelineBreakSimulationNodeRecord,
  nodeById: Map<string, TimelineBreakSimulationNodeRecord>,
): ReactNode {
  const affectedTitles = event.affected_by_event_ids
    .map((eventId) => nodeById.get(eventId)?.title)
    .filter((title): title is string => Boolean(title));

  return (
    <div className="graph-node">
      <div className="graph-node-chronology">{eventChronology(event)}</div>
      <div className="graph-node-title">{event.title}</div>
      <div className="graph-node-era">{event.era ?? "Unclassified era"}</div>
      <div className="graph-node-status">
        {event.status === "broken"
          ? "Removed event"
          : event.status === "invalidated"
            ? "Invalidated"
            : event.status === "unresolved"
              ? "Unresolved"
              : "Active"}
      </div>
      {affectedTitles.length > 0 ? (
        <div className="graph-node-meta">Depends on: {affectedTitles.join(", ")}</div>
      ) : null}
    </div>
  );
}

function toVisualStatus(
  status: TimelineBreakSimulationNodeRecord["status"],
): GraphNodeData["status"] {
  return status === "active" ? "normal" : status;
}

function nodeColor(tone: GraphNodeData["tone"], status: GraphNodeData["status"]): string {
  if (status === "broken") {
    return "#ff727a";
  }
  if (status === "invalidated") {
    return "#ff727a";
  }
  if (status === "unresolved") {
    return "#8893a3";
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
  simulation,
  simulationLoading = false,
  simulateEnabled = false,
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
    () =>
      simulateEnabled && simulation
        ? buildSimulationGraph(simulation)
        : buildCanonicalGraph(graph, simulateEnabled),
    [graph, simulateEnabled, simulation],
  );
  const reactFlowKey = useMemo(
    () =>
      simulateEnabled && simulation
        ? `simulation:${simulation.broken_event_id}:${simulation.nodes.length}:${simulation.edges.length}`
        : `canonical:${graph.focus_event_id}:${graph.nodes.length}:${graph.edges.length}`,
    [graph.edges.length, graph.focus_event_id, graph.nodes.length, simulateEnabled, simulation],
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
          {simulateEnabled
            ? simulationLoading
              ? " Alternate timeline is loading."
              : simulation
                ? " Simulated nodes are rendered as a separate alternate branch."
                : " Preparing alternate timeline."
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
          key={reactFlowKey}
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
        {simulateEnabled ? <span><i className="legend-dot legend-broken" /> Invalidated / broken</span> : null}
        {simulateEnabled ? <span><i className="legend-dot legend-unresolved" /> Unresolved</span> : null}
      </div>
    </div>
  );
}
