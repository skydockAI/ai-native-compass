# Requirements Index

This document indexes all structured requirements for the AI Native Compass (ANC) project.

Source: [Raw Requirements](raw-requirements.md)

---

## Authentication & Session Management

| ID | Title | Priority |
|----|-------|----------|
| [REQ-001](requirements/REQ-001.md) | Local Email/Password Authentication | High |
| [REQ-002](requirements/REQ-002.md) | Active User Login Restriction | High |
| [REQ-003](requirements/REQ-003.md) | Secure Password Storage | High |
| [REQ-004](requirements/REQ-004.md) | Session-Based Authentication | High |
| [REQ-005](requirements/REQ-005.md) | User Self-Service Password Change | Medium |
| [REQ-006](requirements/REQ-006.md) | Admin Password Reset for Users | Medium |
| [REQ-007](requirements/REQ-007.md) | Immediate Access Denial for Archived/Removed Users | High |
| [REQ-008](requirements/REQ-008.md) | Admin User Seeding from Environment | High |
| [REQ-009](requirements/REQ-009.md) | Seeded Admin Protection | High |
| [REQ-010](requirements/REQ-010.md) | SSO-Ready Authentication Design | Medium |

## User Roles & Permissions

| ID | Title | Priority |
|----|-------|----------|
| [REQ-011](requirements/REQ-011.md) | Role Model - Three Roles | High |
| [REQ-012](requirements/REQ-012.md) | Single Role Per User | High |
| [REQ-013](requirements/REQ-013.md) | Admin Role Permissions | High |
| [REQ-014](requirements/REQ-014.md) | Editor Role Permissions | High |
| [REQ-015](requirements/REQ-015.md) | Viewer Role Permissions | High |

## User Entity

| ID | Title | Priority |
|----|-------|----------|
| [REQ-016](requirements/REQ-016.md) | User Entity Definition | High |
| [REQ-017](requirements/REQ-017.md) | User Email Uniqueness | High |
| [REQ-018](requirements/REQ-018.md) | Admin-Only User Management | High |

## Team Entity

| ID | Title | Priority |
|----|-------|----------|
| [REQ-019](requirements/REQ-019.md) | Team Entity Definition | High |
| [REQ-020](requirements/REQ-020.md) | Team Name Uniqueness | High |
| [REQ-021](requirements/REQ-021.md) | Repository-Team Assignment | High |
| [REQ-022](requirements/REQ-022.md) | Team Archive Protection | High |

## Product Entity

| ID | Title | Priority |
|----|-------|----------|
| [REQ-023](requirements/REQ-023.md) | Product Entity Definition | High |
| [REQ-024](requirements/REQ-024.md) | Product Name Uniqueness | High |
| [REQ-025](requirements/REQ-025.md) | Product-Repository Many-to-Many Relationship | High |
| [REQ-026](requirements/REQ-026.md) | Product Archive Protection | High |

## Repository Entity

| ID | Title | Priority |
|----|-------|----------|
| [REQ-027](requirements/REQ-027.md) | Repository Entity Definition | High |
| [REQ-028](requirements/REQ-028.md) | Repository URL Uniqueness | High |
| [REQ-029](requirements/REQ-029.md) | Repository-Template Immutable Assignment | High |
| [REQ-030](requirements/REQ-030.md) | Repository Shared Data Across Products | High |

## Repo Template Entity

| ID | Title | Priority |
|----|-------|----------|
| [REQ-031](requirements/REQ-031.md) | Repo Template Entity Definition | High |
| [REQ-032](requirements/REQ-032.md) | Template Name Uniqueness | High |
| [REQ-033](requirements/REQ-033.md) | Template Archive Protection | High |

## Shared Repository Attributes

| ID | Title | Priority |
|----|-------|----------|
| [REQ-034](requirements/REQ-034.md) | Default Shared Repository Attributes | High |
| [REQ-035](requirements/REQ-035.md) | Custom Shared Attributes | Medium |
| [REQ-036](requirements/REQ-036.md) | Default Shared Attribute Protection | High |

## Template Artifacts

| ID | Title | Priority |
|----|-------|----------|
| [REQ-037](requirements/REQ-037.md) | Template Artifact Structure | High |
| [REQ-038](requirements/REQ-038.md) | Document/Skill/Agent Artifact Values | High |
| [REQ-039](requirements/REQ-039.md) | Other Artifact Value Types | High |
| [REQ-040](requirements/REQ-040.md) | Required Flag for Other Artifacts | Medium |
| [REQ-041](requirements/REQ-041.md) | List Option Lifecycle Management | Medium |

## Template Change Propagation

| ID | Title | Priority |
|----|-------|----------|
| [REQ-042](requirements/REQ-042.md) | Template Artifact Addition Propagation | High |
| [REQ-043](requirements/REQ-043.md) | Template Artifact Rename Propagation | Medium |
| [REQ-044](requirements/REQ-044.md) | Template Artifact Removal Behavior | High |
| [REQ-045](requirements/REQ-045.md) | List Option Editing and Deactivation | Medium |

## CRUD & Archive Behavior

| ID | Title | Priority |
|----|-------|----------|
| [REQ-046](requirements/REQ-046.md) | Soft Delete via Archive | High |
| [REQ-047](requirements/REQ-047.md) | Archived Entity UI Visibility | High |
| [REQ-048](requirements/REQ-048.md) | Permanent Audit History Preservation | High |
| [REQ-049](requirements/REQ-049.md) | Dependency-Based Archive Blocking | High |

## Repository Workflows

| ID | Title | Priority |
|----|-------|----------|
| [REQ-050](requirements/REQ-050.md) | Repository Creation Workflow | High |
| [REQ-051](requirements/REQ-051.md) | Repository Editing Rules | High |
| [REQ-052](requirements/REQ-052.md) | Repository Duplication | Medium |

## Product Management

| ID | Title | Priority |
|----|-------|----------|
| [REQ-053](requirements/REQ-053.md) | Product CRUD Operations | High |
| [REQ-054](requirements/REQ-054.md) | Independent Product-Repository Linking | High |

## Dashboard & UI

| ID | Title | Priority |
|----|-------|----------|
| [REQ-055](requirements/REQ-055.md) | Dashboard-First UI Design | Medium |
| [REQ-056](requirements/REQ-056.md) | Core UI Pages | High |
| [REQ-057](requirements/REQ-057.md) | Dashboard Summary Cards | Medium |
| [REQ-058](requirements/REQ-058.md) | List Filtering Capabilities | Medium |

## Audit Logging

| ID | Title | Priority |
|----|-------|----------|
| [REQ-059](requirements/REQ-059.md) | Audit Log Events | High |
| [REQ-060](requirements/REQ-060.md) | Audit Log Entry Structure | High |
| [REQ-061](requirements/REQ-061.md) | Audit Log Access Control | High |
| [REQ-062](requirements/REQ-062.md) | Audit Log UI | Medium |

## Deployment & Infrastructure

| ID | Title | Priority |
|----|-------|----------|
| [REQ-063](requirements/REQ-063.md) | PostgreSQL Database | High |
| [REQ-064](requirements/REQ-064.md) | Docker Compose Deployment | High |
| [REQ-065](requirements/REQ-065.md) | Host-Mounted Persistent Storage | High |

## Non-Functional Requirements

| ID | Title | Priority |
|----|-------|----------|
| [REQ-066](requirements/REQ-066.md) | Simplicity and Maintainability | Medium |
| [REQ-067](requirements/REQ-067.md) | UI Usability | Medium |
| [REQ-068](requirements/REQ-068.md) | Security Best Practices | High |
| [REQ-069](requirements/REQ-069.md) | Data Integrity Enforcement | High |

---

## Summary

- **Total requirements**: 69
- **High priority**: 50
- **Medium priority**: 19
- **Low priority**: 0
