# TASKS.md

> **This file is the backlog and planning layer.** It is for capturing ideas, design notes, and items not yet ready to be worked on.
> 
> **It is not the work queue.** Active work is tracked as GitHub Issues assigned to a milestone.
> To see what's in scope for the current release, run:
> ```
> gh issue list --milestone v0.2.0
> ```
> Items graduate from here to GitHub Issues when they are scoped and ready to be worked.

---

## Up next
- [ ] Rich text formatting for Description (and possibly Review/Personal Note) fields
  - Options: lightweight Markdown editor (e.g. EasyMDE) on the form + Markdown-to-HTML render on detail page, or a simple WYSIWYG toolbar
  - Existing plain-text descriptions should still render cleanly (Markdown parsers handle this gracefully)
- [ ] Login Security Enhancements
  - Implement Rate Limiting: look at Flask-Limiter or a similar library to prevent brute force attacks.
  - Failed Login Count: Track the number of failed login attempts in a database table (e.g., failed_logins) for persistent tracking.
  - Alerting: Add a threshold to send email alerts (e.g., after 5 failed attempts from the same IP). This might not be necessary as Google ReCaptcha might head this off.
- [ ] Add Google ReCaptcha to password reset form
- [ ] Unknown IP
  - Add functionality to see if the user who just logged in had ever logged in from their current IP address. If not, send email.
  - Ignore initial login.
- [ ] Add Distillery (and Bottler) detail pages
  - Currently, clicking a distillery link anywhere on the site routes directly to a filtered bottle list. There is no page that represents the distillery itself as a destination.
  - The Distillery model already has description, location, and url fields — none of which are currently surfaced anywhere after add/edit.
  - Create a distillery detail page (e.g. /charlie/distillery/0001) that displays the distillery's name, description, location, and a link to their external URL, followed by a list of the user's bottles from that distillery.
  - Update all distillery links site-wide (bottle detail page, distillery list) to route to this new detail page rather than directly to the filtered bottle list.
  - Apply the same pattern to Bottlers, which has the same issue.
- [ ] Audit imports. 
  - Should they be `from mywhiskies.blueprints.core.models import bottle_distillery` or `from mywhiskies.blueprints import core`?
  - The latter would mean the reference in the template would be `core.models.bottle_distillery` which is more self-documenting as to the location of the import.
- [ ] "My Account" enhancements:
  - Allow user to update email/password
  - All of the rules of registration apply (unique email, password validation, user must confirm email)
  - Add an option to make the entire account private
- [ ] Registration enhancements
  - Add options to register with Google|Facebook|Apple|etc
  - Should we add an option to not have a password, but when a user logs in send them a text or email with a code? How would that impact existing users?
- [ ] Export Data enhancements
  - Currently export to CSV. Give option for JSON? Other formats?
  - Allow options to include: killed bottles, private bottles, and personal notes (all are currently included by default, but user might want to share exported data with others)
- [ ] Clean up the registration view file (verify this still needs to be done)
  - Lots of business logic that should be abstracted out into a service file.
- [ ] Server-side image resizing on upload (Pillow → S3) [backend]
  - Remove hard size restriction; resize to ~1200px on long edge before storing
- [ ] Set up https for local development


## Backlog
- [ ] Pro tier — add is_pro flag to user model [schema]
  - Gate features behind it now; build payment flow later
- [ ] Pro tier — retain full-res images alongside resized versions [backend]
  - Store {uuid}_1_full.jpg + {uuid}_1.jpg in S3
- [ ] Pro tier — AI label scan to prefill bottle fields [feature]
  - Claude vision API reads bottle label image → prefills name, distillery, type, ABV, etc.
- [ ] Distilleries list URL cleanup: /charlie/distilleries [backend]


## Completed
- [x] Mobile fixes on bottle detail page
  - Breadcrumb no longer wraps across multiple lines
  - h1 title font size reduced on small screens
  - Action buttons replaced with a kebab (⋮) dropdown on mobile; desktop layout unchanged
  - Bottle image column scoped to flex only on lg+ to prevent horizontal overflow
- [x] Reorganize bottle list controls
  - Random Bottle and Filter List moved to header row alongside the page title
  - Search, Show Killed, Theme, and Per page remain in the controls row
- [x] Filter List — disable type options the user has no bottles of
- [x] Clean up form templates
  - Macro (`form_utils`) was already in place; no changes needed
  - Combined add/edit into a single `form.html` per domain (bottle, bottler, distillery)
  - Normalized bottler/distillery headers to use the page-header-line breadcrumb pattern
- [x] HTMX — replace image carousel on bottle detail page
  - Carousel uses Bootstrap + vanilla JS; no jQuery dependency
- [x] Add "delete" button on bottle detail page
  - Inside of conditional with edit button.
  - Add modal confirmation. Which means it's likely time to break the modal confirmation out into its own template.
- [x] Bottle detail page: fix Prev/Next button alignment on carousel
  - Buttons currently span full panel width (`justify-content-between`); consider centering them under the image instead
- [x] Extend bottle search to match description, bottler name, and distillery name (server-side filter in `list_bottles_by_user`, `list_bottles_for_entity`, and `get_random_bottle`)
- [x] Improve UI when users have multiple bottles with the same name (e.g., single barrels or duplicates) by grouping and optionally supporting quantities.
  - Group bottles in list view by shared product attributes (e.g., name, distillery).
  - Show a single collapsed row per group with an expandable “+” toggle to view individual bottles.
  - Expanded view should include bottle-specific data (e.g., open/killed dates, barrel #, bottle #, notes).
- [x] GitHub found 31 vulnerabilities on charliegriefer/my-whiskies's default branch (1 critical, 10 high, 19 moderate, 1 low). To find out more, visit https://github.com/charliegriefer/my-whiskies/security/dependabot
- [x] High Priority: Some bottle detail pages are showing broken images. But when I go to edit those pages, I see the images.
  - Example: https://my-whiskies.online/charlie/bottle/0147
- [x] HTMX migration + overhaul of bottles list page [frontend/backend]
  - Replace DataTables + jQuery with HTMX + server-side rendering; remove jQuery dependency
  - Must preserve: type filter (checkbox dropdown), "Show Killed Bottles" toggle, free-text search, pagination, column sorting, edit/delete icons, "Random Bottle" button, image indicator icon
  - Truncate long text fields (description etc.) with ellipsis; show full text on hover via Bootstrap tooltip
  - Reconsider what columns to show — table may be displaying too much; needs to look good on mobile
  - Discuss whether to show/hide the "incognito" icon for private bottles in the list
  - Surface single barrel status visually in the list (icon? badge?)
  - Overall: lots to discuss before coding — plan first
- [x] Add `is_single_barrel` boolean field to Bottle model [schema]
  - Migration + badge on bottle detail page; pick group table deferred
- [x] Audit tests
  - Do I have adequate test coverage? If not, let's add new tests.
  - Is my testing infrastructure sound? Do any of my fixtures need to be addressed? Any other structural concerns?
- [x] Rewrite the README.md
- [x] Clean up the bottle detail page [frontend]
- [x] Ensure that user names are unique, and constrained to alphanumeric and potentially a few safe special characters (stick with underscore and hyphen for now) [backend]
  - Uniqueness should be case-insensitive. e.g. "CHARLIE" is the same as "charlie", and should not be allowed.
  - We added new URL routes yesterday that will feature the username more prominently in the URL (e.g. /charlie/bottle/0001, /charlie/distillery/0001, /charlie/bottler/0001). This is a minor nit, but I'd like the username in the URL to be lowercased, even if the actual username has uppercase characters. Can that be done? Will it mess up routing?
- [x] Claude Code /init — CLAUDE.md generated
- [x] Add user-scoped numeric IDs to bottle and distillery models [schema]
  - user_bottle_num, user_distillery_num — sequential per user, ordered by date_created
- [x] New URL routes: /charlie/bottle/0001 and /charlie/distillery/0001 [backend]
  - 301 redirects from old UUID URLs