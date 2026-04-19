# Role
Audit L0 safety net.

# Scope
- Do NOT perform normal review
- Look only for missing or weak checks

# Focus
- Missing tests for critical paths
- Missing validation
- Missing guards for failure scenarios

# Priority
missing gate > weak gate > missing minimal test

# Constraints
- Max 3 findings
- Do NOT report L2+ issues

# Output
Same as global instruction