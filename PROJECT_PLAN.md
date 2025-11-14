# PROJECT_PLAN.md

# Pips Solver – Project Plan

## 1. Project Overview

We are building an AI solver for the NYT puzzle PIPS, where the goal is to place domino tiles (0–6) onto a grid divided into colored regions, each with its own logical rule (equal, distinct, sum, >n, <n). 
Tiles occupy two adjacent cells, must be fully in-bounds, and cannot overlap.

This puzzle naturally fits a Constraint Satisfaction Problem (CSP):

- **Variables:** tile placements or cell assignments  
- **Domains:** all legal orientations and placements  
- **Constraints:** non-overlap, bounds, and region rule satisfaction  

We will implement two solvers covered in class:

1. Systematic CSP Search (backtracking + heuristics)  
2. Local Search (hill climbing, stochastic variants, random restarts, simulated annealing)

We will evaluate performance across Easy, Medium, and Hard puzzles.


## 2. Course Topics covered

Our approach uses search methods from class:

### **CSP Concepts**
- CSP modeling with variables, domains, and constraints  
- Backtracking search  
- Domain pruning through early constraint checking  
- Variable-ordering heuristics:
  - Degree heuristic
  - MRV-style reasoning (most constrained variable)

### **Local Search**
- Hill climbing (first-choice and stochastic)  
- Handling local optima  
- Random restarts  
- Simulated annealing  


## 3. Milestones

### **A. Puzzle Representation (CSP Model)**

Implement the core data structures:

- Grid and region partitions  
- Region constraint types  
- Domino tiles, orientations, and possible placements  
- CSP structure:
  - Variables = tiles or cells  
  - Domains = legal placements  
  - Constraints = overlap, adjacency, region rules
  - 

### **B. Baseline Solvers**

#### **1. Baseline CSP Backtracking**
- Recursive backtracking with incremental constraint checks  
- Reject partial assignments that violate:
  - Region rules  
  - Overlap  
  - Bounds  
- Track nodes expanded and backtracks  

This sets the baseline for a systematic search.

#### **2. Baseline Local Search**
- Generate a random complete assignment  
- Score assignment using a constraint-violation function  
- Apply:
  - First-choice hill climbing  
  - Stochastic hill climbing  
  - Random restarts  
  - Optional simulated annealing  

This provides a contrasting non-systematic solver.

### **C. CSP Solver With Heuristics**

Extend the backtracking solver with heuristics from class:

- **Degree Heuristic:** prioritize variables with many constraints
- **MRV-style Heuristic:** choose variables with few remaining legal placements
- **Forward-Checking-Style Pruning:** remove invalid neighbor domain values after each assignment

Evaluation will compare:
- Plain backtracking  
- Backtracking with heuristics  

### **D. Enhanced Strategies**

Within the class framework, explore:

- Region-prioritized ordering (assign constrained regions early)  
- Improved pruning based on partial region feasibility  
- Local search initialization strategies for faster convergence  

### **E. Evaluation Framework**

For Easy, Medium, and Hard puzzles, measure:

- Runtime
- Nodes expanded
- Backtracking count
- Success rate of local search
- Effects of heuristics and restarts
- Stability across random seeds

Present results using plots, tables, and comparative metrics.


## 4. Team Responsibilities

### **Member 1 — Representation + Local Search**
- Implement puzzle parser and CSP representation
- Build hill-climbing and stochastic local search solvers
- Add random restarts and simulated annealing
- Define constraint-based objective function
- Review backtracking implementation

### **Member 2 — CSP Backtracking**
- Implement baseline backtracking
- Add constraint checking (overlap, bounds, region rules)
- Coordinate variable/domain structures with Member 1
- Review heuristic modules

### **Member 3 — CSP Heuristics**
- Implement degree heuristic
- Implement MRV-style variable ordering
- Add forward-checking-style domain pruning
- Integrate heuristics into the backtracking solver
- Analyze performance improvements

### **Member 4 — Evaluation & Experimentation (involves all AI solver methods)**
- Build an automated experiment runner
- Collect runtime and search statistics
- Tune parameters for local search
- Produce result tables, plots, and analyses
- Validate puzzle model through testing

