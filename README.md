# delay-tolerant-networks

# Delay Tolerant Networks (DTN) Simulator

## Project Overview
A comprehensive DTN simulator implementing BLE/Wi-Fi Direct protocols with 3D visualization and multiple routing algorithms for academic research.

**Team Size:** 6 members (3 pairs)  
**Duration:** 10 weeks  
**Course:** Computer Networks  

## Team Structure
- **Pair 1:** Core Networking & Protocols (PHY/Network layers)
- **Pair 2:** Mobility & Data Management (Movement models/Experiments)  
- **Pair 3:** GUI & Visualization (3D interface/Analytics)

## Git Workflow & Branch Strategy

### Branch Structure
```
main (production-ready code)
├── staging (integration testing)
├── feature/pair1-phy-ble
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
- `feature/pair1-phy-ble-discovery`
- `feature/pair2-mobility-contact-plans`
- `hotfix/buffer-overflow-fix`

#### 2. Merge Request (MR) Process

**MANDATORY WORKFLOW:**
1. **Feature → Staging:** Requires 1 approval from another pair + automated tests passing
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

**Review assignment:**
- Pair 1 reviews Pair 2/3 code
- Pair 2 reviews Pair 1/3 code  
- Pair 3 reviews Pair 1/2 code

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
[PAIR1] FEAT: Implement BLE discovery protocol
[PAIR2] FIX: Contact plan CSV parser edge cases  
[PAIR3] REFACTOR: Optimize 3D rendering performance
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
cd dtn-simulator

# Install dependencies
npm install  # or pip install -r requirements.txt

# Setup pre-commit hooks
pre-commit install

# Run initial tests
npm test  # or pytest
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
- **Issue labels:** `pair1`, `pair2`, `pair3`, `bug`, `enhancement`, `urgent`
- **Milestones:** Major deliverables and sprint goals

### Issue Creation Standards
**Template:**
```markdown
## Description
[Clear description of task/bug]

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
- `#pair1-networking` - PHY/Network layer updates
- `#pair2-mobility` - Mobility/Data management  
- `#pair3-gui` - Visualization discussions
- `#integration` - Cross-pair coordination
- `#blockers` - Urgent issues needing help

### Meeting Cadence
- **Daily standups:** 15 min, async updates in Slack
- **Sprint planning:** Every 2 weeks, 2 hours
- **Retrospectives:** End of each sprint, 1 hour
- **Integration sync:** Weekly, 1 hour across pairs

## Conflict Resolution

### Code Conflicts
1. Try to resolve through discussion
2. Escalate to team lead if needed
3. Use pair programming sessions for complex integration
4. Document decisions in GitHub issues

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
