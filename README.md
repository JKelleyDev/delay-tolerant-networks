# Delay Tolerant Networks (DTN) Simulator

## Project Overview
A comprehensive DTN simulator implementing satellite communication or BLE/Wi-Fi Direct protocols with 3D visualization and multiple routing algorithms for academic research.

**Team Size:** 6 members (3 pairs)  
**Duration:** 10 weeks (5 two-week sprints)  
**Course:** Computer Networks  

## Team Structure
- **Pair 1:** Core Networking & Protocols (PHY/Network layers)
- **Pair 2:** Mobility & Data Management (Movement models/Experiments)  
- **Pair 3:** GUI & Visualization (3D interface/Analytics)

## Sprint Plan Overview

### Sprint 1 (Weeks 1-2): Foundation & Architecture Decision
**Goal:** Establish architecture and make satellite vs terrestrial decision

**Pair 1 - Core Networking:**
- Bundle layer foundation (IDs, TTL, basic message structure)
- **Decision point: Satellite vs BLE/Wi-Fi Direct by end of week 1**
- PHY abstraction layer with chosen technology stubs
- Simple Epidemic routing as proof-of-concept
- Define networking APIs for other pairs

**Pair 2 - Mobility & Data:**
- Contact plan CSV parser (works for both satellite and terrestrial)
- **If satellite:** Orbital mechanics basics and satellite contact windows
- **If terrestrial:** Random Waypoint mobility model
- Experiment framework setup and data collection interfaces
- Node state tracking and logging foundation

**Pair 3 - GUI & Visualization:**
- 3D map framework with basic node rendering
- **Satellite consideration:** Earth globe view vs flat terrain
- Project UI shell and basic controls
- Geographic/orbital coordinate system and camera controls

### Sprint 2 (Weeks 3-4): Core Implementation
**Goal:** Implement primary features for chosen technology

**Pair 1 - Core Networking:**
- Complete all 3 routing algorithms (Epidemic, PRoPHET, Spray-and-Wait)
- **Satellite route:** Orbital contact prediction, high-latency/high-bandwidth links
- **Terrestrial route:** BLE and Wi-Fi Direct with contact capacity
- Basic ARQ adapted for chosen technology
- Buffer management foundation

**Pair 2 - Mobility & Data:**
- **Satellite route:** Satellite constellation mobility, ground station locations
- **Terrestrial route:** Contact plan execution + community mobility model
- Metrics collection system (delivery ratio, delay, overhead)
- Experiment parameter management for chosen scenario

**Pair 3 - GUI & Visualization:**
- **Satellite route:** 3D Earth with satellite orbits and ground stations
- **Terrestrial route:** Node movement animation on terrain
- Real-time contact visualization (satellite passes or terrestrial encounters)
- Basic control panels (run/pause/reset)
- Performance metrics display framework

### Sprint 3 (Weeks 5-6): Advanced Features
**Goal:** Add sophisticated DTN features for chosen technology

**Pair 1 - Core Networking:**
- **Satellite route:** Long delay tolerance, store-and-forward optimization
- **Terrestrial route:** Sliding window ARQ and BER-driven errors
- Fragmentation and reassembly
- Custody transfer mechanism adapted for technology choice
- Advanced buffer policies (oldest/largest/random drop)

**Pair 2 - Mobility & Data:**
- **Satellite route:** Orbital parameter changes, satellite failures/recovery
- **Terrestrial route:** Mid-run contact plan modification system
- Duplicate suppression and restoration logic
- Statistical analysis tools for experiments
- Delivery delay distribution tracking

**Pair 3 - GUI & Visualization:**
- **Satellite route:** Satellite pass predictions, coverage maps, ground track visualization
- **Terrestrial route:** Contact schedule Gantt charts, animated bundle paths
- Buffer fill level bars per node
- **Technology toggle:** Instead of BLE/Wi-Fi, show different satellite bands or terrestrial modes
- Timeline controls for long-duration satellite scenarios

### Sprint 4 (Weeks 7-8): Integration & Experiments
**Goal:** System integration and begin experimental validation

**Pair 1 - Core Networking:**
- System integration and optimization
- **Satellite route:** Multi-hop satellite routing, constellation coordination
- **Terrestrial route:** Connectivity restoration after partition healing
- Fine-tune routing algorithm parameters for chosen technology
- Performance profiling and bottleneck fixes

**Pair 2 - Mobility & Data:**
- Execute experiments E1 (protocol comparison) and E2 (buffer sizes)
- **Satellite route:** Before/after analysis for orbital changes or satellite failures
- **Terrestrial route:** Before/after analysis for contact plan changes
- Statistical validation and confidence intervals
- Data export functionality

**Pair 3 - GUI & Visualization:**
- Complete all visualization features for chosen technology
- **Satellite route:** 3D satellite constellation views, coverage analysis
- **Terrestrial route:** All terrestrial visualization features
- Export capabilities for charts and data
- Demo mode and presentation views

### Sprint 5 (Weeks 9-10): Final Experiments & Presentation
**Goal:** Complete validation and prepare deliverables

**Pair 1 - Core Networking:**
- Final bug fixes and edge case handling
- Code documentation and reproducibility
- Performance validation across all scenarios
- Technical presentation preparation

**Pair 2 - Mobility & Data:**
- Complete experiment E3 (TTL impact - especially relevant for satellite delays)
- Comprehensive results analysis and insights
- Statistical writeup and interpretation
- Experimental methodology documentation

**Pair 3 - GUI & Visualization:**
- Final UI polish and demo preparation
- Results visualization and presentation graphics
- User manual and demo script
- Video/screenshot capture for presentation

## Technology Decision Factors

**Choose Satellite if:**
- Team has stronger math/physics background for orbital mechanics
- Want to focus on long-delay, high-capacity DTN scenarios
- Interested in space-based networking applications
- Prefer predictable contact patterns

**Choose Terrestrial if:**
- Team prefers more complex mobility and discovery scenarios
- Want to implement multiple wireless technologies
- Interested in opportunistic networking applications
- Prefer more dynamic, unpredictable contact patterns

## Git Workflow & Branch Strategy

### Branch Structure
```
main (production-ready code)
├── staging (integration testing)
├── feature/pair1-phy-technology
├── feature/pair1-network-routing
├── feature/pair2-mobility-models
├── feature/pair2-experiments
├── feature/pair3-3d-visualization
└── feature/pair3-control-panels
```

### Development Rules

#### 1. Branch Naming Convention
- **Feature branches:** `feature/[pair#]-[component]-[description]`
- **Hotfix branches:** `hotfix/[issue-description]`
- **Release branches:** `release/sprint-[number]`

**Examples:**
- `feature/pair1-phy-satellite-contacts`
- `feature/pair1-phy-ble-discovery` 
- `feature/pair2-mobility-orbital-mechanics`
- `feature/pair2-mobility-contact-plans`
- `hotfix/buffer-overflow-fix`

#### 2. Merge Request (MR) Process

**MANDATORY WORKFLOW:**
1. **Feature → Staging:** Requires 1 approval from another person.
2. **Staging → Main:** Requires 2 approvals from different pairs + full test suite passing

**MR Requirements:**
- [ ] Descriptive title and summary of changes
- [ ] Link to related GitHub issue/task
- [ ] Screenshots/demos for GUI changes
- [ ] Unit tests written and passing
- [ ] Code follows project style guide
- [ ] Documentation updated if needed

#### 3. Code Review Standards

**Reviewers must check:**
- Code quality and readability
- Adherence to DTN requirements
- Integration compatibility with other pairs
- Performance implications
- Test coverage

#### 4. Commit Standards

**Format:** `[PAIR#] [TYPE]: Brief description`

**Types:**
- `FEAT:` New feature implementation
- `FIX:` Bug fix
- `REFACTOR:` Code restructuring
- `TEST:` Adding/updating tests
- `DOCS:` Documentation changes
- `STYLE:` Code formatting changes

**Examples:**
```
[PAIR1] FEAT: Implement satellite orbital contact prediction
[PAIR1] FEAT: Implement BLE discovery protocol
[PAIR2] FIX: Contact plan CSV parser edge cases  
[PAIR3] REFACTOR: Optimize 3D Earth rendering performance
```

#### 5. Protected Branches

**Main Branch Protection:**
- No direct pushes allowed
- Requires passing CI/CD checks
- Requires 2 approving reviews
- Dismiss stale reviews when new commits pushed
- Requires branches to be up to date before merging

**Staging Branch Protection:**
- No direct pushes allowed  
- Requires 1 approving review
- Requires passing automated tests

## Development Environment

### Required Setup
```bash
# Clone repository
git clone [repo-url]

# Install dependencies
npm install  # or pip install -r requirements.txt
```

### IDE Configuration
- **Recommended:** VS Code with team settings (`.vscode/settings.json`)
- **Required extensions:** ESLint, Prettier, GitLens
- **Code formatter:** Prettier (auto-format on save)

## Testing Strategy

### Automated Testing (CI/CD)
- **Unit tests:** Each pair maintains >80% coverage
- **Integration tests:** Cross-pair interface testing
- **Performance tests:** Memory usage, rendering FPS
- **Linting:** Code style enforcement

### Manual Testing Checkpoints
- **Weekly integration:** Friday staging deployments
- **Sprint demos:** Every 2 weeks to course instructor
- **Final integration:** Week 9 full system test

## Issue Tracking & Project Management

### GitHub Projects Setup
- **Sprint boards:** 2-week sprints with burndown charts
- **Issue labels:** `pair1`, `pair2`, `pair3`, `bug`, `enhancement`, `urgent`, `satellite`, `terrestrial`
- **Milestones:** Major deliverables and sprint goals

### Issue Creation Standards
**Template:**
```markdown
## Description
[Clear description of task/bug]

## Technology Context
- [ ] Satellite implementation
- [ ] Terrestrial implementation  
- [ ] Technology agnostic

## Acceptance Criteria
- [ ] Criterion 1
- [ ] Criterion 2

## Pair Assignment
@pair1-member1 @pair1-member2

## Dependencies
- Depends on #[issue-number]

## Definition of Done
- [ ] Code implemented and reviewed
- [ ] Tests written and passing
- [ ] Documentation updated
- [ ] Integrated with staging
```

## Communication Protocols

### Slack/Discord Channels
- `#general` - General project discussion
- `#architecture-decisions` - Technology choice discussions
- `#pair1-networking` - PHY/Network layer updates
- `#pair2-mobility` - Mobility/Data management  
- `#pair3-gui` - Visualization discussions
- `#integration` - Cross-pair coordination
- `#blockers` - Urgent issues needing help

### Meeting Cadence
- **Daily standups:** 15 min, async updates in discord (with pair partner)
- **Sprint planning:** Every 2 weeks, 1 hour
- **Technology decision meeting:** Week 1, all pairs required
- **Retrospectives:** End of each sprint, 30 minutes
- **Integration sync:** Weekly, 1 hour across pairs

## Conflict Resolution

### Code Conflicts
1. Try to resolve through discussion
2. Escalate to team lead if needed
3. Use pair programming sessions for complex integration
4. Document decisions in GitHub issues

### Technology Decision Conflicts
1. Present pros/cons analysis by end of Week 1
2. Team vote if no consensus
3. Document decision rationale in repository

### Merge Conflicts
1. **Responsibility:** Person merging resolves conflicts
2. **Complex conflicts:** Schedule pair/team session
3. **Breaking changes:** Require team discussion before merge

## Quality Gates

### Before Staging Merge
- [ ] Feature complete per acceptance criteria
- [ ] Unit tests passing (>80% coverage)
- [ ] Code reviewed and approved
- [ ] No breaking changes to other pairs' work
- [ ] Performance impact assessed
- [ ] Compatible with chosen technology path

### Before Main Merge
- [ ] Full integration testing completed
- [ ] All automated tests passing
- [ ] Documentation updated
- [ ] Demo-ready functionality
- [ ] Approved by 2+ team members from different pairs

---

## Quick Reference Commands

```bash
# Start new feature
git checkout staging
git pull origin staging
git checkout -b feature/pair1-new-feature

# Submit for review
git push origin feature/pair1-new-feature
# Create MR: feature/pair1-new-feature → staging

# Deploy to staging (after MR approval)
git checkout staging
git pull origin staging
# Automated deployment triggers

# Hotfix workflow
git checkout main
git pull origin main  
git checkout -b hotfix/critical-issue
# ... make fix ...
git push origin hotfix/critical-issue
# Create MR: hotfix/critical-issue → main (requires 2 approvals)
```

**Questions?** Check our [Wiki](wiki-url) or ask in `#general` channel.
