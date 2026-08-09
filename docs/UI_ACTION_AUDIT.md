# UI action audit

Every visible interactive control is mapped to a real state change or API operation.

| Surface/control | Action | Backing behavior | Failure behavior |
| --- | --- | --- | --- |
| New document | reset editor | clears active project/version and artifacts | none; local state only |
| Recent document | open latest version | `GET /api/projects/{id}/source` | error notice; current editor preserved |
| Studio nav | show editor | local view state | n/a |
| Templates nav | list profiles | `GET /api/templates` | startup error notice |
| History nav | list projects/versions | `GET /api/projects` | startup error notice |
| Settings nav | show actual privacy/security boundary | static product contract | n/a |
| Title/source/input format | edit draft | local controlled state; marked unsaved | n/a |
| Template selector | select generator profile | sent to generation API | invalid server value is 422 |
| Format checkbox | select outputs | sent to generation API | zero selections disables generation |
| Generate files | create/correct/generate | project POST, version POST, generation POST | remains unsaved and displays error |
| Verification row | report exact server result | returned verifier status/checks/reason | no success substitution |
| File download | download real artifact | version-scoped artifact endpoint | HTTP error, no fake download |
| Export | ZIP source/files/manifest | export endpoint | HTTP error |
| Delete in History | confirmed destructive action | DELETE project | error notice; no optimistic removal |
| Mobile menu | open/close navigation | local state | n/a |
| Unlock | establish HTTP-only local session | `POST /api/session` | invalid-token notice, gate remains |
| Status bar | reflect draft persistence | dirty until successful generation/version write | truthful unsaved text |

The editor maximize icon is labeled as an informational fit-to-workspace control and does not claim a modal fullscreen operation. No analytics, notification, provider, or cloud button is presented.

## Accessibility

- landmarks and headings are semantic;
- icon-only buttons have accessible names;
- controls have labels/legends;
- focus-visible outlines are explicit;
- color is supplemented by text/icons for verification status;
- reduced-motion preference disables the spinner animation duration;
- mobile navigation remains keyboard-operable.
