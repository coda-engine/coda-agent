# Coda Agent Tool Registry

This document defines the currently integrated tools (MCP Virtual Bridge) availability, versions, and usage protocols.

## Tool Overview

| Tool Name | Version | Description | Backend Engine |
|-----------|---------|-------------|----------------|
| **Generic VRP** | 1.1.0 | Vehicle Routing Problem Solver (CVRP, VRPTW, PDP) | OR-Tools / Google Cloud Run |
| **CP-SAT** | 2.3.0 | Constraint Programming Solver | OR-Tools CP-SAT |
| **MILP Solver** | 1.0.0 | Mixed-Integer Linear Programming | OR-Tools (SCIP/GLOP) |
| **Min Cost Flow** | 1.0.0 | Network Flow Optimization (Min Cost) | OR-Tools |
| **Max Flow** | 1.0.0 | Network Bottleneck Analysis | OR-Tools |
| **Linear Assignment** | 1.0.0 | 1-to-1 Worker/Task Assignment | OR-Tools |
| **Continuous Linear** | 1.0.0 | Continuous Linear Programming (GLOP) | OR-Tools (GLOP) |
| **T-Test** | 1.0.0 | Statistical Hypothesis Testing | SciPy / StatsModels |

## Integration Details

**Location**: `backend/app/tools/<tool_name>/schema.json`  
**Bridge Service**: `backend/app/services/tools_bridge.py`  
**System Instructions**: `backend/app/core/prompts.py`

## Tool Schemas

### 1. Generic VRP (v1.1.0)
- **Endpoint**: `/` (POST)
- **Key Features**: 
  - Arbitrary dimensions (weight, volume, time).
  - Relations (pickup/delivery, sequence).
  - Time Windows.

### 2. CP-SAT (v2.3.0)
- **Endpoint**: `/` (POST)
- **Key Features**:
  - `no_overlap`, `cumulative`, `all_different` constraints.
  - Interval variables.
  - Boolean logic constraints.

### 3. Linear & MILP (v1.0.0)
- **Endpoint**: `/` (POST)
- **Key Features**:
  - Supports INT, BOOL, and CONTINUOUS variables.
  - Linear constraints (`<=`, `>=`, `==`).
  - Solvers: SCIP (Mixed Integer), GLOP (Linear).

### 4. Continuous Linear (v1.0.0)
- **Endpoint**: `/` (POST)
- **Key Features**:
  - Pure continuous optimization.
  - Sensitivity analysis (Shadow prices).

### 5. Min Cost Flow (v1.0.0)
- **Endpoint**: `/` (POST)
- **Key Features**:
  - Network graph (Nodes, Edges).
  - Supply/Demand balance.

### 6. Simple Max Flow (v1.0.0)
- **Endpoint**: `/` (POST)
- **Key Features**:
  - Source -> Sink throughput.

### 7. Linear Sum Assignment (v1.0.0)
- **Endpoint**: `/` (POST)
- **Key Features**:
  - Cost matrix minimization.
  - Unbalanced assignment support.

### 8. T-Test (v1.0.0)
- **Endpoint**: `/solve_stats_ttest` (POST)
- **Key Features**:
  - Independent, Paired, and One-Sample T-tests.
  - Raw data or Summary stats input.
