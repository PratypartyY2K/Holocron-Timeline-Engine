"use client";

import type { Route } from "next";
import dagre from "@dagrejs/dagre";
import {
  Background,
  Controls,
  MarkerType,
  MiniMap,
  Position,
  ReactFlow,
  type Edge,
  type Node,
  type NodeMouseHandler,
  type ReactFlowInstance,
} from "@xyflow/react";
import { useRouter } from "next/navigation";
import { useCallback, useEffect, useMemo, useRef, useState, type ReactNode } from "react";
import "@xyflow/react/dist/style.css";

import { CAUSAL_EDGE_TYPES } from "./causal-edge";
import type {
  CausalGraphResponse,
  CausalGraphEdgeRecord,
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

type GraphColorMode = "tone" | "era" | "faction";

type GraphNodeData = {
  label: ReactNode;
  slug: string;
  tone: "dependency" | "focus" | "consequence";
  status: "normal" | "deactivated" | "broken" | "invalidated" | "unresolved";
};

type GraphSourceNode = EventRecord | TimelineBreakSimulationNodeRecord;

type GraphSource = {
  brokenEventId?: string;
  depth: number;
  edges: CausalGraphEdgeRecord[];
  nodes: GraphSourceNode[];
};

type GraphBuildResult = {
  edges: Edge[];
  nodes: Node<GraphNodeData>[];
};

type PathSelection = {
  edges: Set<string>;
  nodes: Set<string>;
};

type ColorRulebookEntry = {
  color: string;
  description: string;
  label: string;
};

const DEFAULT_EDGE_OPTIONS = Object.freeze({
  style: {
    stroke: "rgba(233, 180, 76, 0.55)",
    strokeWidth: 1.6,
  },
});
const FIT_VIEW_OPTIONS = Object.freeze({ padding: 0.2 });
const PRO_OPTIONS = Object.freeze({ hideAttribution: true });
const NODE_ORIGIN: [number, number] = [0, 0];

const NODE_WIDTH = 240;
const NODE_MIN_HEIGHT = 136;
const NODE_VERTICAL_GAP = 48;
const CHRONOLOGY_COLUMN_GAP = 320;
const LAYOUT_MARGIN_X = 80;
const LAYOUT_MARGIN_Y = 60;
const GRAPH_ACCENT_PALETTE = [
  "#e9b44c",
  "#70c1b3",
  "#ff9ba7",
  "#9fb3ff",
  "#f28482",
  "#84a59d",
  "#f6bd60",
  "#b8de6f",
];

function formatChronology(year: number): string {
  if (year < 0) {
    return `${Math.abs(year)} BBY`;
  }
  if (year > 0) {
    return `${year} ABY`;
  }
  return "0 ABY";
}

function eventChronology(event: GraphSourceNode): string {
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
      <div className="graph-node-meta">
        {event.faction_names.length > 0 ? event.faction_names.join(", ") : "No faction tags"}
      </div>
    </div>
  );
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
      <div className="graph-node-meta">
        {event.faction_names.length > 0 ? event.faction_names.join(", ") : "No faction tags"}
      </div>
      {affectedTitles.length > 0 ? (
        <div className="graph-node-meta">Depends on: {affectedTitles.join(", ")}</div>
      ) : null}
    </div>
  );
}

function estimatedLineCount(value: string, charactersPerLine: number): number {
  if (value.trim().length === 0) {
    return 0;
  }
  return Math.max(1, Math.ceil(value.length / charactersPerLine));
}

function nodeHeightForEvent(
  event: GraphSourceNode,
  nodeById: Map<string, GraphSourceNode>,
): number {
  let lineCount = 0;

  lineCount += 1;
  lineCount += estimatedLineCount(event.title, 18);
  lineCount += 1;

  const factionLine = event.faction_names.length > 0 ? event.faction_names.join(", ") : "No faction tags";
  lineCount += estimatedLineCount(factionLine, 24);

  if ("status" in event) {
    lineCount += 1;
    if (event.affected_by_event_ids.length > 0) {
      const affectedLine = `Depends on: ${event.affected_by_event_ids
        .map((eventId) => nodeById.get(eventId)?.title)
        .filter((title): title is string => Boolean(title))
        .join(", ")}`;
      lineCount += estimatedLineCount(affectedLine, 22);
    }
  }

  return Math.max(NODE_MIN_HEIGHT, 28 + lineCount * 20);
}

function toVisualStatus(
  status: TimelineBreakSimulationNodeRecord["status"] | "normal" | "deactivated",
): GraphNodeData["status"] {
  return status === "active" ? "normal" : status;
}

function nodeColor(tone: GraphNodeData["tone"], status: GraphNodeData["status"]): string {
  if (status === "broken" || status === "invalidated") {
    return "#ff727a";
  }
  if (status === "unresolved" || status === "deactivated") {
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

function hashToPaletteIndex(value: string): number {
  let hash = 0;
  for (const char of value) {
    hash = (hash * 31 + char.charCodeAt(0)) >>> 0;
  }
  return hash % GRAPH_ACCENT_PALETTE.length;
}

function nodeAccent(event: GraphSourceNode, colorMode: GraphColorMode): string {
  if (colorMode === "tone") {
    return "#e9b44c";
  }
  if (colorMode === "era") {
    const key = event.era ?? "unclassified-era";
    return GRAPH_ACCENT_PALETTE[hashToPaletteIndex(key)];
  }
  const key = factionColorKey(event);
  return GRAPH_ACCENT_PALETTE[hashToPaletteIndex(key)];
}

function factionColorKey(event: GraphSourceNode): string {
  if (event.faction_names.length === 0) {
    return "unaligned";
  }
  if (event.faction_names.length === 1) {
    return event.faction_names[0];
  }
  return [...event.faction_names].sort((left, right) => left.localeCompare(right)).join(" + ");
}

function colorRulebookEntries(
  source: GraphSource,
  colorMode: GraphColorMode,
): ColorRulebookEntry[] {
  if (colorMode === "tone") {
    return [
      {
        label: "Dependency",
        color: "#70c1b3",
        description: "Upstream events that support the focused event.",
      },
      {
        label: "Focus event",
        color: "#e9b44c",
        description: "The currently selected event at the center of this graph.",
      },
      {
        label: "Consequence",
        color: "#ff9ba7",
        description: "Downstream events affected by the focused event.",
      },
    ];
  }

  if (colorMode === "era") {
    return Array.from(
      new Map(
        source.nodes
          .map((event) => {
            const label = event.era ?? "Unclassified era";
            return [
              label,
              {
                label,
                color: nodeAccent(event, "era"),
                description: "Nodes in this era share this accent color.",
              } satisfies ColorRulebookEntry,
            ] as const;
          }),
      ).values(),
    ).sort((left, right) => left.label.localeCompare(right.label));
  }

  return Array.from(
    new Map(
      source.nodes
        .map((event) => {
          const key = factionColorKey(event);
          const label = key === "unaligned" ? "Unaligned" : key;
          return [
            label,
            {
              label,
              color: nodeAccent(event, "faction"),
              description:
                key === "unaligned"
                  ? "Events with no faction tags."
                  : event.faction_names.length > 1
                    ? "Events tagged with this exact faction combination."
                    : "Events tagged to this faction.",
            } satisfies ColorRulebookEntry,
          ] as const;
        }),
    ).values(),
  ).sort((left, right) => left.label.localeCompare(right.label));
}

function toneForNode(
  nodeId: string,
  focusEventId: string,
  incoming: Map<string, string[]>,
  outgoing: Map<string, string[]>,
): GraphNodeData["tone"] {
  if (nodeId === focusEventId) {
    return "focus";
  }

  const dependencyDistance = new Map<string, number>([[focusEventId, 0]]);
  const dependencyQueue: string[] = [focusEventId];
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

  const consequenceDistance = new Map<string, number>([[focusEventId, 0]]);
  const consequenceQueue: string[] = [focusEventId];
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

  return (dependencyDistance.get(nodeId) ?? 0) < 0 ? "dependency" : "consequence";
}

function computePathSelection(
  edges: CausalGraphEdgeRecord[],
  startNodeId: string | null,
  endNodeId: string | null,
): PathSelection {
  if (!startNodeId || !endNodeId || startNodeId === endNodeId) {
    return { edges: new Set(), nodes: new Set(startNodeId ? [startNodeId] : []) };
  }

  const outgoing = new Map<string, Array<{ edgeId: string; targetId: string }>>();
  for (const edge of edges) {
    const bucket = outgoing.get(edge.source_id) ?? [];
    bucket.push({ edgeId: edge.id, targetId: edge.target_id });
    outgoing.set(edge.source_id, bucket);
  }

  const path =
    findDirectedPath(outgoing, startNodeId, endNodeId) ??
    findDirectedPath(outgoing, endNodeId, startNodeId);
  if (!path) {
    return {
      edges: new Set(),
      nodes: new Set([startNodeId, endNodeId]),
    };
  }

  return {
    edges: new Set(path.edgeIds),
    nodes: new Set(path.nodeIds),
  };
}

function findDirectedPath(
  outgoing: Map<string, Array<{ edgeId: string; targetId: string }>>,
  startNodeId: string,
  endNodeId: string,
): { edgeIds: string[]; nodeIds: string[] } | null {
  const queue: string[] = [startNodeId];
  const previous = new Map<string, { edgeId: string; fromNodeId: string }>();

  while (queue.length > 0) {
    const current = queue.shift();
    if (current === undefined) {
      break;
    }
    if (current === endNodeId) {
      break;
    }

    for (const next of outgoing.get(current) ?? []) {
      if (next.targetId === startNodeId || previous.has(next.targetId)) {
        continue;
      }
      previous.set(next.targetId, { edgeId: next.edgeId, fromNodeId: current });
      queue.push(next.targetId);
    }
  }

  if (startNodeId !== endNodeId && !previous.has(endNodeId)) {
    return null;
  }

  const edgeIds: string[] = [];
  const nodeIds: string[] = [endNodeId];
  let cursor = endNodeId;
  while (cursor !== startNodeId) {
    const step = previous.get(cursor);
    if (!step) {
      return null;
    }
    edgeIds.unshift(step.edgeId);
    nodeIds.unshift(step.fromNodeId);
    cursor = step.fromNodeId;
  }

  return { edgeIds, nodeIds };
}

function groupIncomingAndOutgoing(edges: CausalGraphEdgeRecord[]): {
  incoming: Map<string, string[]>;
  outgoing: Map<string, string[]>;
} {
  const incoming = new Map<string, string[]>();
  const outgoing = new Map<string, string[]>();
  for (const edge of edges) {
    const nextOutgoing = outgoing.get(edge.source_id) ?? [];
    nextOutgoing.push(edge.target_id);
    outgoing.set(edge.source_id, nextOutgoing);

    const nextIncoming = incoming.get(edge.target_id) ?? [];
    nextIncoming.push(edge.source_id);
    incoming.set(edge.target_id, nextIncoming);
  }
  return { incoming, outgoing };
}

function buildGraph(
  source: GraphSource,
  {
    colorMode,
    pathSelection,
    pathAnchorId,
    simulateEnabled,
  }: {
    colorMode: GraphColorMode;
    pathSelection: PathSelection;
    pathAnchorId: string | null;
    simulateEnabled: boolean;
  },
): GraphBuildResult {
  const { incoming, outgoing } = groupIncomingAndOutgoing(source.edges);
  const eventById = new Map(source.nodes.map((node) => [node.id, node]));
  const sortedEvents = [...source.nodes].sort((left, right) => {
    const leftRank = "topological_rank" in left ? left.topological_rank : 0;
    const rightRank = "topological_rank" in right ? right.topological_rank : 0;
    if (leftRank !== rightRank) {
      return leftRank - rightRank;
    }
    if (left.start_year !== right.start_year) {
      return left.start_year - right.start_year;
    }
    return left.title.localeCompare(right.title);
  });

  const chronologyYears = Array.from(new Set(sortedEvents.map((event) => event.start_year))).sort(
    (left, right) => left - right,
  );
  const chronologyColumnByYear = new Map(chronologyYears.map((year, index) => [year, index]));
  const nodeHeightById = new Map(
    sortedEvents.map((event) => [event.id, nodeHeightForEvent(event, eventById)]),
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
      height: nodeHeightById.get(event.id) ?? NODE_MIN_HEIGHT,
    });
  }

  for (const edge of source.edges) {
    dagreGraph.setEdge(edge.source_id, edge.target_id);
  }

  dagre.layout(dagreGraph);

  const hasPathSelection = pathSelection.nodes.size > 1 || pathSelection.edges.size > 0;
  const focusEventId = source.brokenEventId ?? source.nodes[0]?.id ?? "";

  const nodes: Node<GraphNodeData>[] = sortedEvents.map((event) => {
    const tone = toneForNode(event.id, focusEventId, incoming, outgoing);
    const layoutNode = dagreGraph.node(event.id);
    const chronologyColumn = chronologyColumnByYear.get(event.start_year) ?? 0;
    const nodeHeight = nodeHeightById.get(event.id) ?? NODE_MIN_HEIGHT;
    const accent = nodeAccent(event, colorMode);
    const isOnPath = pathSelection.nodes.has(event.id);
    const isAnchor = pathAnchorId === event.id;
    const status =
      "status" in event
        ? toVisualStatus(event.status)
        : (simulateEnabled ? "deactivated" : "normal");

    return {
      id: event.id,
      type: "default",
      width: NODE_WIDTH,
      height: nodeHeight,
      position: {
        x: LAYOUT_MARGIN_X + chronologyColumn * CHRONOLOGY_COLUMN_GAP,
        y: layoutNode.y - nodeHeight / 2,
      },
      className: `graph-node-shell graph-node-shell-${status}`,
      style: {
        borderColor: accent,
        minHeight: `${nodeHeight}px`,
        boxShadow: isAnchor
          ? `0 0 0 3px ${accent}55, 0 18px 45px rgba(0, 0, 0, 0.22)`
          : undefined,
        opacity: hasPathSelection && !isOnPath ? 0.38 : 1,
      },
      sourcePosition: Position.Right,
      targetPosition: Position.Left,
      data: {
        label:
          "status" in event
            ? buildSimulationLabel(event, eventById as Map<string, TimelineBreakSimulationNodeRecord>)
            : buildLabel(event),
        slug: event.slug,
        tone,
        status,
      },
      draggable: false,
    };
  });

  const nodesByColumn = new Map<number, Node<GraphNodeData>[]>();
  for (const node of nodes) {
    const event = eventById.get(node.id);
    const chronologyColumn = event ? (chronologyColumnByYear.get(event.start_year) ?? 0) : 0;
    const columnNodes = nodesByColumn.get(chronologyColumn) ?? [];
    columnNodes.push(node);
    nodesByColumn.set(chronologyColumn, columnNodes);
  }

  for (const columnNodes of nodesByColumn.values()) {
    columnNodes.sort((left, right) => left.position.y - right.position.y);

    let previousBottom = Number.NEGATIVE_INFINITY;
    for (const node of columnNodes) {
      const nodeHeight = typeof node.height === "number" ? node.height : NODE_MIN_HEIGHT;
      const minY = previousBottom + NODE_VERTICAL_GAP;
      if (node.position.y < minY) {
        node.position.y = minY;
      }
      previousBottom = node.position.y + nodeHeight;
    }
  }

  const edges: Edge[] = source.edges.map((edge) => {
    const targetNode = eventById.get(edge.target_id);
    const edgeOnPath = pathSelection.edges.has(edge.id);
    const accent = targetNode ? nodeAccent(targetNode, colorMode) : "#e9b44c";
    const targetStatus = targetNode && "status" in targetNode ? targetNode.status : null;

    return {
      id: edge.id,
      source: edge.source_id,
      target: edge.target_id,
      type: "causal",
      markerEnd: { type: MarkerType.ArrowClosed },
      animated: edgeOnPath,
      sourcePosition: Position.Right,
      targetPosition: Position.Left,
      style:
        edgeOnPath
          ? {
              stroke: accent,
              strokeWidth: 3.6,
            }
          : targetStatus === "invalidated"
            ? {
                stroke: "rgba(255, 114, 122, 0.92)",
                strokeWidth: 2.4,
                opacity: hasPathSelection ? 0.3 : 1,
              }
            : targetStatus === "unresolved"
              ? {
                  stroke: "rgba(136, 147, 163, 0.92)",
                  strokeWidth: 2,
                  strokeDasharray: "6 4",
                  opacity: hasPathSelection ? 0.3 : 1,
                }
              : {
                  stroke: accent,
                  strokeWidth: 1.8,
                  opacity: hasPathSelection ? 0.2 : 0.9,
                },
      data: {
        note: edge.note ?? "",
      },
    };
  });

  return { nodes, edges };
}

function selectionLabel(source: GraphSource, startNodeId: string | null, endNodeId: string | null): string {
  const nodeById = new Map(source.nodes.map((node) => [node.id, node]));
  if (!startNodeId) {
    return "Click one node to anchor a path. Click a second node to highlight the causal route between them.";
  }
  if (!endNodeId || startNodeId === endNodeId) {
    return `Anchor: ${nodeById.get(startNodeId)?.title ?? "Unknown event"}. Choose another node to trace the path.`;
  }
  const startTitle = nodeById.get(startNodeId)?.title ?? "Unknown event";
  const endTitle = nodeById.get(endNodeId)?.title ?? "Unknown event";
  return `Tracing path between ${startTitle} and ${endTitle}. Double-click any node to open its detail page.`;
}

function currentSource(
  graph: CausalGraphResponse,
  simulation: TimelineBreakSimulationResponse | null | undefined,
  simulateEnabled: boolean,
): GraphSource {
  if (simulateEnabled && simulation) {
    return {
      brokenEventId: simulation.broken_event_id,
      depth: graph.depth,
      edges: simulation.edges,
      nodes: simulation.nodes,
    };
  }

  return {
    brokenEventId: graph.focus_event_id,
    depth: graph.depth,
    edges: graph.edges,
    nodes: graph.nodes,
  };
}

function hasGraphNode(source: GraphSource, nodeId: string | null): boolean {
  if (nodeId === null) {
    return false;
  }
  return source.nodes.some((node) => node.id === nodeId);
}

export function EventFocusGraph({
  graph,
  simulation,
  simulationLoading = false,
  simulateEnabled = false,
}: EventFocusGraphProps) {
  const router = useRouter();
  const [hoveredNote, setHoveredNote] = useState<string | null>(null);
  const [colorMode, setColorMode] = useState<GraphColorMode>("tone");
  const [pathStartNodeId, setPathStartNodeId] = useState<string | null>(null);
  const [pathEndNodeId, setPathEndNodeId] = useState<string | null>(null);
  const [reactFlowInstance, setReactFlowInstance] = useState<ReactFlowInstance | null>(null);
  const clickTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const defaultEdgeOptions = useMemo(() => DEFAULT_EDGE_OPTIONS, []);
  const fitViewOptions = useMemo(() => FIT_VIEW_OPTIONS, []);
  const proOptions = useMemo(() => PRO_OPTIONS, []);

  const miniMapNodeColor = useCallback(
    (node: Node) =>
      nodeColor(
        (node.data as GraphNodeData).tone,
        (node.data as GraphNodeData).status,
      ),
    [],
  );

  const activeSource = useMemo(
    () => currentSource(graph, simulation, simulateEnabled),
    [graph, simulateEnabled, simulation],
  );

  const pathSelection = useMemo(
    () => computePathSelection(activeSource.edges, pathStartNodeId, pathEndNodeId),
    [activeSource.edges, pathEndNodeId, pathStartNodeId],
  );

  const reactFlowGraph = useMemo(
    () =>
      buildGraph(activeSource, {
        colorMode,
        pathSelection,
        pathAnchorId: pathStartNodeId,
        simulateEnabled,
      }),
    [activeSource, colorMode, pathSelection, pathStartNodeId, simulateEnabled],
  );

  const rulebookEntries = useMemo(
    () => colorRulebookEntries(activeSource, colorMode),
    [activeSource, colorMode],
  );

  const handleHoverNoteChange = useCallback((note: string | null) => {
    setHoveredNote((current) => (current === note ? current : note));
  }, []);

  const handleClearPath = useCallback(() => {
    if (clickTimeoutRef.current !== null) {
      clearTimeout(clickTimeoutRef.current);
      clickTimeoutRef.current = null;
    }
    setHoveredNote(null);
    setPathStartNodeId(null);
    setPathEndNodeId(null);
  }, []);

  const handleNodeClick = useCallback<NodeMouseHandler>(
    (_, node) => {
      if (clickTimeoutRef.current !== null) {
        clearTimeout(clickTimeoutRef.current);
      }
      clickTimeoutRef.current = setTimeout(() => {
        setPathStartNodeId((currentStart) => {
          if (currentStart === null) {
            setPathEndNodeId(null);
            return node.id;
          }
          if (currentStart === node.id) {
            setPathEndNodeId(null);
            return null;
          }
          setPathEndNodeId(node.id);
          return currentStart;
        });
        clickTimeoutRef.current = null;
      }, 220);
    },
    [],
  );

  const handleNodeDoubleClick = useCallback<NodeMouseHandler>(
    (event, node) => {
      event.preventDefault();
      event.stopPropagation();
      if (clickTimeoutRef.current !== null) {
        clearTimeout(clickTimeoutRef.current);
        clickTimeoutRef.current = null;
      }
      const slug = (node.data as GraphNodeData).slug;
      router.push(`/events/${slug}` as Route);
    },
    [router],
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

  const pathSummary = useMemo(
    () => selectionLabel(activeSource, pathStartNodeId, pathEndNodeId),
    [activeSource, pathEndNodeId, pathStartNodeId],
  );

  useEffect(() => {
    return () => {
      if (clickTimeoutRef.current !== null) {
        clearTimeout(clickTimeoutRef.current);
      }
    };
  }, []);

  useEffect(() => {
    if (!hasGraphNode(activeSource, pathStartNodeId)) {
      setPathStartNodeId(null);
      setPathEndNodeId(null);
      return;
    }
    if (!hasGraphNode(activeSource, pathEndNodeId)) {
      setPathEndNodeId(null);
    }
  }, [activeSource, pathEndNodeId, pathStartNodeId]);

  useEffect(() => {
    if (!reactFlowInstance) {
      return;
    }
    const timeoutId = setTimeout(() => {
      void reactFlowInstance.fitView({ padding: 0.2 });
    }, 0);
    return () => clearTimeout(timeoutId);
  }, [reactFlowGraph.edges, reactFlowGraph.nodes, reactFlowInstance]);

  return (
    <div className="graph-shell">
      <div className="graph-header">
        <div>
          <p className="section-kicker">Graph View</p>
          <h2>Focused causal map</h2>
        </div>
        <p className="timeline-caption">
          Visualizing actual <code>CAUSES</code> edges within depth {activeSource.depth}. Use
          click-to-anchor path tracing and switch node coloring by graph tone, era, or faction.
          {simulateEnabled
            ? simulationLoading
              ? " Alternate timeline is loading."
              : simulation
                ? " Simulated nodes are rendered in the same graph with status-based styling."
                : " Preparing alternate timeline."
            : ""}
        </p>
      </div>

      <div className="graph-toolbar">
        <label className="filter-field graph-filter-field">
          <span>Node color</span>
          <select value={colorMode} onChange={(event) => setColorMode(event.target.value as GraphColorMode)}>
            <option value="tone">Graph tone</option>
            <option value="era">Era</option>
            <option value="faction">Faction</option>
          </select>
        </label>
        <button
          type="button"
          className="secondary-link graph-clear-button"
          onClick={handleClearPath}
        >
          Clear path
        </button>
      </div>

      <div className="graph-rulebook">
        <div className="graph-rulebook-header">
          <span className="graph-rulebook-label">Color rulebook</span>
          <p className="graph-rulebook-copy">
            {colorMode === "tone"
              ? "Colors represent graph role."
              : colorMode === "era"
                ? "Colors represent Star Wars era groupings in the current graph."
                : "Colors represent faction tagging in the current graph."}
          </p>
        </div>
        <div className="graph-rulebook-grid">
          {rulebookEntries.map((entry) => (
            <article key={`${colorMode}:${entry.label}`} className="graph-rulebook-card">
              <div className="graph-rulebook-swatch-row">
                <i
                  className="graph-rulebook-swatch"
                  style={{ backgroundColor: entry.color }}
                  aria-hidden="true"
                />
                <strong>{entry.label}</strong>
              </div>
              <p>{entry.description}</p>
            </article>
          ))}
        </div>
      </div>

      <div className="graph-note-panel" aria-live="polite">
        <span className="graph-note-label">Path inspector</span>
        <p className="graph-note-copy">{hoveredNote ?? pathSummary}</p>
      </div>

      <div className="graph-canvas">
        <ReactFlow
          nodes={reactFlowGraph.nodes}
          edges={edgesWithHoverData}
          fitView
          fitViewOptions={fitViewOptions}
          proOptions={proOptions}
          nodesDraggable={false}
          nodesConnectable={false}
          elementsSelectable
          edgeTypes={CAUSAL_EDGE_TYPES}
          defaultEdgeOptions={defaultEdgeOptions}
          nodeOrigin={NODE_ORIGIN}
          zoomOnDoubleClick={false}
          onInit={setReactFlowInstance}
          onNodeClick={handleNodeClick}
          onNodeDoubleClick={handleNodeDoubleClick}
        >
          <MiniMap
            pannable
            position="top-right"
            zoomable
            style={{ width: 140, height: 88 }}
            nodeColor={miniMapNodeColor}
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
