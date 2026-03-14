# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Hugo static site for an academic resume/CV, using the `hugo-devresume-theme`. The site is hosted on GitHub Pages and outputs to the `docs/` directory instead of the default `public/`.

## Common Commands

```bash
# Development server - runs at localhost:1313
hugo server

# Build the site (outputs to docs/)
hugo

# Build with drafts included
hugo --buildDrafts
```

## Architecture

### Configuration Structure

- **config.toml**: Main configuration file containing all personal data including profile, education, publications, skills, and contact information
- **publishDir = "docs"**: Site builds to `docs/` for GitHub Pages deployment
- **theme = "hugo-devresume-theme"**: Uses the custom theme

### Theme Structure

The theme uses a single-page layout with partial templates:

- **layouts/index.html**: Main page template that includes partials conditionally
- **layouts/partials/**: Modular sections (header, summary, education, skills, awards, information, social, footer)

Key partials:
- `profile.html`: Name, tagline, avatar
- `summary.html`: Biography text
- `education.html`: Academic history
- `information.html`: Publications list (most active section)
- `skills.html`: Technical skills
- `awards.html`: Honors and awards
- `contact.html`: Contact links
- `social.html`: Social media links

### Content Management

All content is managed via `config.toml` under `[params]` sections:

- `[params.profile]`: Name, avatar (`me.png`), tagline
- `[params.education]`: List of degrees with university and dates
- `[params.information]`: Publications with title, authors, publisher, href, details
- `[params.skills]`: Categorized skill lists
- `[params.awards]`: Honors with name, body, date
- `[params.contact]`: Email, location, external links
- `[params.social]`: GitHub and other social links

### Assets

- **docs/assets/images/**: Contains `me.png` (profile photo) and `avatar.png`
- **static/**: Empty (content is served from theme's static folder)
- **docs/**: Generated site output committed to repo for GitHub Pages

## Important Notes

- The `docs/` folder contains the generated site and is committed to git for GitHub Pages hosting
- After running `hugo`, commit the changes in `docs/` to update the live site
- The theme's SCSS is pre-built; custom styling requires editing theme files or overriding in `config.toml` (primaryColor, textPrimaryColor)
- Avatar image path in config: `avatar = "me.png"` (relative to assets/images)
