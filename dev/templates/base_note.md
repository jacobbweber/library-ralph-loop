---
id: "202310271200"
title: "Base Note Template"
type: "zettelkasten"
tags: [template, base]
categories: [system]
created: "2023-10-27"
modified: "2023-10-27"
status: "stable"
summary: "A stable base note template for the Ralph Loop library."
---

# Base Note Template

This is a stable base note template. It contains all required metadata fields and valid values.

## Structure

- **id**: Unique identifier (YYYYMMDDHHMM)
- **title**: Note title
- **type**: Note type (e.g., zettelkasten, diwk)
- **tags**: List of tags
- **categories**: List of categories
- **created**: Creation date (YYYY-MM-DD)
- **modified**: Modification date (YYYY-MM-DD)
- **status**: Note status (raw, draft, review, stable)
- **summary**: Single-sentence description

## Usage

Copy this file to `dev/library/` and modify the content and metadata as needed. Ensure the `status` is set to `stable` before promoting to production.
