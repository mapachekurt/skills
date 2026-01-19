---
name: skillz-creator
description: Guide for creating effective skills. Use this skill when you want to create a new skill (or update an existing skill) that extends Claude's capabilities with specialized knowledge, workflows, or tool integrations. Includes one-click installation capability documentation.
license: Complete terms in LICENSE.txt
---

# Skillz Creator

This skill provides guidance for creating effective skills that can be installed with a single click.

## About Skills

Skills are modular, self-contained packages that extend Claude's capabilities by providing specialized knowledge, workflows, and tools. They transform Claude from general-purpose into a specialized agent with procedural knowledge.

## Quick Start: Create a Skill

### Step 1: Use This Skill
Ask Claude: "Create a skill for [your task/domain]"

### Step 2: Specify Your Skill
Provide:
- **Name**: Unique identifier (e.g., `vertex-ai-reasoning-config`)
- **Description**: What it does and when to use it
- **Content**: SKILL.md with instructions
- **Optional Resources**: Scripts, references, or assets

### Step 3: Get .skill File
Claude packages everything as a single `.skill` file and presents it here in chat.

### Step 4: One-Click Install
- File appears in chat with **[Install skill]** button
- Click once
- Skill is immediately available across all Claude agents
- No configuration needed

## Core Principles

### Concise is Key
Only add context Claude doesn't have. Challenge each piece of information: "Does Claude really need this explanation?"

### Appropriate Degrees of Freedom
- **High freedom**: Text instructions when multiple approaches are valid
- **Medium freedom**: Scripts with parameters when a pattern exists
- **Low freedom**: Specific scripts when operations are fragile

## Skill Anatomy

```
skillz-creator/
├── SKILL.md (required)
│   ├── YAML frontmatter (name, description, license)
│   └── Markdown instructions
└── Optional Resources
    ├── scripts/       - Executable code
    ├── references/    - Documentation
    └── assets/        - Templates, icons, etc.
```

## SKILL.md Format

**Frontmatter (YAML):**
```yaml
---
name: your-skill-name
description: Clear description of what skill does and when to use it
license: MIT (or other)
---
```

**Body (Markdown):**
- Instructions and guidance
- Examples
- Common use cases
- Troubleshooting

## One-Click Installation

**This is the key benefit:**

1. Skill is created as a single `.skill` file (ZIP archive)
2. User downloads or opens the file
3. Claude Desktop detects it automatically
4. **[Install skill]** button appears
5. One click installs it
6. No file copying, no configuration
7. Skill is immediately available

**This is why the .skill format matters:**
- Users don't need to understand skill structure
- No manual file organization
- Pure one-click experience
- Professional distribution method

## Creating Your Skill

When you want a new skill:

1. **Tell Claude**: "Create a skill for [task]"
2. **Specify**: Name, description, what it does
3. **Get**: .skill file with [Install skill] button
4. **Click**: One button to install
5. **Use**: Immediately in any prompt

## Best Practices

### Do's
- ✅ Clear, concise descriptions
- ✅ Include "when to use" information
- ✅ Bundle all resources in one .skill file
- ✅ Use YAML frontmatter correctly
- ✅ Include troubleshooting guides

### Don'ts
- ❌ Long verbose explanations
- ❌ Scattered resources
- ❌ Missing description
- ❌ Unclear naming conventions

## Common Skill Types

| Type | Use Case | Example |
|------|----------|---------|
| API Integration | Working with specific APIs | Vertex AI, Stripe, GitHub |
| Document Work | Creating/editing files | DOCX, PDF, PPTX |
| Workflow | Multi-step processes | n8n flows, deployment pipelines |
| Domain Knowledge | Company/industry specific | Financial schemas, legal templates |
| Automation | Repetitive tasks | Data processing, batch operations |

## Iteration Workflow

1. Create and install skill
2. Use it on real tasks
3. Notice improvements needed
4. Update SKILL.md or resources
5. Repackage as .skill
6. One click to update

## Quick Validation Checklist

- [ ] Name is unique and descriptive
- [ ] Description includes when to use
- [ ] YAML frontmatter is correct
- [ ] SKILL.md body has clear instructions
- [ ] All referenced scripts/files included
- [ ] Packaged as single .skill file
- [ ] [Install skill] button appears in Claude

---

**Status**: Ready to use  
**Version**: 1.0  
**Updated**: 2025-01-19  
**One-Click Install**: Yes ✓