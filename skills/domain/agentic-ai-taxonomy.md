# Skill: Agentic AI Taxonomy

**Domain**: domain
**Activation triggers**: Agent architecture, Agentic AI, Copilot, AI Agent, autonomy levels, HITL, HOTL, perception-action loop
**References**: CLAUDE.md §4.2, specs/system/02-agent-design.md, ADR-0004, ADR-0023

---

## Canonical Definitions

Use these definitions exactly. Do not redefine without creating an ADR.

| Term                  | Definition                                                                                                                                                      | Source                                 |
| --------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------- |
| **AI Agent**          | Software that perceives its environment, reasons about it, and takes actions to achieve a goal — but within a single, bounded task                              | Russell & Norvig (2021)                |
| **Agentic AI**        | An AI system with an autonomous, continuous cycle of **perception → reasoning → action → learning**, capable of multi-step planning across dynamic environments | CLAUDE.md §4.2                         |
| **Copilot (IR)**      | An Agentic AI that **augments** human capacity without replacing it — presents options, proposes actions, executes only with approval                           | CLAUDE.md §4.2                         |
| **HITL**              | Human-in-the-Loop — agent proposes, **human must approve before any action executes**                                                                           | ADR-0023                               |
| **HOTL**              | Human-on-the-Loop — agent acts automatically, **human monitors and may override at any time**                                                                   | CLAUDE.md §4.2                         |
| **Guardrail**         | Executable technical control that constrains or validates agent actions                                                                                         | CLAUDE.md §4.2                         |
| **Autonomy boundary** | The precise set of action types an agent may or may not take without human approval                                                                             | specs/ethics/16-autonomy-boundaries.md |

---

## AI Agent vs Agentic AI vs Copilot

```
AI Agent          Agentic AI              Copilot (IR)
─────────         ────────────────────    ────────────────────────────
Single task       Continuous cycle        Continuous cycle +
Bounded context   Multi-step planning     human oversight at
No persistence    Persistent memory       every consequential
                  Goal-directed           action (HITL)
                  Self-improving
```

**When to use each term in this project:**

- Use **Agentic AI** when describing the system architecture or research framing.
- Use **Copilot** when describing the human–AI interaction model (augmentation, not replacement).
- Use **AI Agent** only when referring to a single specialist agent (DetectionAgent, TriageAgent, etc.).

---

## Autonomy Spectrum

```
FULLY MANUAL                                              FULLY AUTONOMOUS
     │                                                              │
     ├── Human decides ──► Human acts
     │
     ├── HITL ──► Agent proposes ──► Human approves ──► Agent executes
     │           (RemediationAgent for PRODUCTION_* actions)
     │
     ├── HOTL ──► Agent acts ──► Human monitors ──► Human may override
     │           (DetectionAgent, TriageAgent, RCAAgent, PostMortemAgent)
     │
     └── BLOCKED ──► Action prohibited regardless of approval
                     (PRODUCTION_data_delete, PRODUCTION_iam_change)
```

The Copilot operates at HITL for all production remediation and HOTL for all
detection/triage/RCA/post-mortem tasks. Fully autonomous production action is
architecturally prohibited.

---

## The Perception-Action Loop

```
┌─────────────────────────────────────────────────────┐
│                  AGENTIC AI LOOP                    │
│                                                     │
│  ┌──────────┐   ┌──────────┐   ┌──────────────┐   │
│  │PERCEPTION│──►│ REASONING│──►│    ACTION    │   │
│  │          │   │          │   │              │   │
│  │ Logs     │   │ LLM      │   │ HITL gate ──►│   │
│  │ Metrics  │   │ inference│   │ Approved?    │   │
│  │ Traces   │   │ + schema │   │ Execute /    │   │
│  │ Runbooks │   │ validation│  │ Escalate     │   │
│  └──────────┘   └──────────┘   └──────────────┘   │
│        ▲                               │           │
│        │         LEARNING              │           │
│        └───── Post-mortem feedback ────┘           │
│               + bias audit                         │
└─────────────────────────────────────────────────────┘
```

Each loop iteration writes an event to the immutable audit trail (ADR-0024) before any
action is taken or output is produced.

---

## Multi-Agent Architecture Patterns

### Pattern 1: Orchestrator + Specialists (this project — ADR-0004)

```
OrchestratorAgent
  ├── DetectionAgent   (HOTL) — anomaly detection
  ├── TriageAgent      (HOTL) — severity classification
  ├── RCAAgent         (HOTL) — root cause analysis
  ├── RemediationAgent (HITL) — action proposal + execution
  └── PostMortemAgent  (HOTL) — incident documentation
```

**When to use:** Incident response, complex multi-step workflows with clearly separated
concerns and different autonomy requirements per stage.

### Pattern 2: Peer-to-Peer (not used in this project)

Agents negotiate and delegate without a central orchestrator. Harder to audit and
enforce HITL — not suitable for production systems requiring full accountability.

### Pattern 3: Hierarchical (not used in this project)

Manager agent delegates to sub-agents that may delegate further. Adds latency and
complicates HITL chain of custody.

---

## HITL / HOTL Decision Heuristics

Use HITL when the action:

- Modifies production infrastructure (scale, config, restart, traffic shift)
- Is irreversible or hard to reverse within the incident window
- Could cause a wider outage if incorrectly applied
- Involves secrets or IAM

Use HOTL when the action:

- Is read-only or informational (anomaly scan, severity classification, hypothesis)
- Is easily overridden by the on-call engineer
- Does not directly change production state
- Produces a recommendation, not an execution

Never auto-execute on HITL timeout — always escalate to a human (ADR-0023).

---

## Common Mistakes to Avoid

| Mistake                                    | Correct approach                                                          |
| ------------------------------------------ | ------------------------------------------------------------------------- |
| Calling the system "autonomous"            | It is a Copilot — human oversight is always available                     |
| Equating HOTL with "no oversight"          | HOTL means always-overridable, not unmonitored                            |
| Adding a new PRODUCTION\_\* action as HOTL | All PRODUCTION\_\* actions are HITL by default (spec 16)                  |
| Comparing to chatbot                       | Agentic AI has a persistent action loop; chatbots respond to single turns |
| Using "AI" and "Agent" interchangeably     | "AI Agent" is a specific architectural pattern, not a synonym for AI      |
