# Copyright 2021 Xanadu Quantum Technologies Inc.

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

#     http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Functionality for applying cuts to the circuit graph"""
from pennylane.cut.mark import MeasureNode, PrepareNode, OperationNode, WireCut, GateCut
import networkx as nx
from typing import Tuple, Dict, Sequence, Any
from pennylane.operation import Operator


def apply_cuts(g):
    original_nodes = tuple(g.nodes)

    for n in original_nodes:
        if isinstance(n, WireCut):
            _remove_wire_cut_node(n, g)
        if isinstance(n, GateCut):
            _remove_gate_cut_node(n, g)


def find_cuts(g: nx.Graph, wire_capacity: int, gate_capacity: int, **kwargs) -> \
        Tuple[Tuple[Tuple[Operator, Operator, Any]], Tuple[Operator], Tuple[Tuple[Operator]], Dict]:
    nodes = list(g.nodes)
    wire_cuts = ((nodes[0], nodes[1], 0),)
    gate_cuts = (nodes[2],)
    partitioned_nodes = ((nodes[0],), (nodes[1],) + tuple(nodes[3:]))
    return wire_cuts, gate_cuts, partitioned_nodes, {}


def place_cuts(g: nx.Graph, wire_capacity: int, gate_capacity: int, **kwargs):
    wire_cuts, gate_cuts, partitioned_nodes, opt_results = find_cuts(g, wire_capacity, gate_capacity, **kwargs)

    for n in gate_cuts:
        _remove_gate_cut_node(n, g)

    for op1, op2, wire in wire_cuts:
        meas = MeasureNode(wires=wire)
        prep = PrepareNode(wires=wire)
        g.add_node(meas)
        g.add_node(prep)
        g.add_edge(op1, meas)
        g.add_edge(prep, op2)


def _remove_wire_cut_node(n, g):
    predecessors = g.predecessors(n)
    successors = g.successors(n)

    g.remove_node(n)

    for p in predecessors:
        for wire in p.wires:
            if wire in n.wires:
                op = MeasureNode(wires=wire)
                g.add_node(op)
                g.add_edge(p, op)

    for s in successors:
        for wire in s.wires:
            if wire in n.wires:
                op = PrepareNode(wires=wire)
                g.add_node(op)
                g.add_edge(op, s)


def _remove_gate_cut_node(n, g):
    predecessors = list(g.predecessors(n))
    successors = list(g.successors(n))

    g.remove_node(n)

    n_wires = n.wires

    for wire in n_wires:
        p_wire = [p for p in predecessors if wire in p.wires][0]
        s_wire = [s for s in successors if wire in s.wires][0]

        op = OperationNode(wires=wire)
        g.add_node(op)
        g.add_edge(p_wire, op)
        g.add_edge(op, s_wire)
