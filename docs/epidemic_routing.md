# Epidemic Routing (P1-002/A1)

## Overview
This document describes the **Epidemic Routing** algorithm implemented for the DTN (Delay Tolerant Network) simulator.  
It defines the routing behavior, duplicate suppression, and summary vector exchange mechanisms.

## Key Responsibilities
- Flood bundles to all available contacts.
- Use anti-entropy to exchange summary vectors.
- Suppress duplicate bundles efficiently.
- Prioritize transmission based on TTL and importance.
- Respect contact window constraints.

## Class Diagram
```mermaid
classDiagram
    class EpidemicRouter {
        +route_bundle(bundle)
        +exchange_summary_vector(peer)
        +calculate_transmission_priority(bundle)
        -bundle_history : Dict
        -contact_windows : List
    }
