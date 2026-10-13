# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Users

Sales and business-development teams managing early-stage B2B prospects locally.

## Product Purpose

LeadOps helps users capture potential customers, assess their sales progress, and keep the next outreach action visible. Success is a reliable local workflow for turning a prospect into a managed lead.

## Positioning

A self-hosted, local-first lead workspace focused on the essential prospect record and outreach pipeline before research automation or CRM integrations.

## Operating Context

Users add and review company prospects during daily sales work, search the pipeline, update statuses, and refer to recent records from a dashboard.

## Capabilities and Constraints

- Lead records persist through a FastAPI, SQLAlchemy, PostgreSQL backend.
- V1 supports dashboard metrics and lead create, read, update, delete, search, filtering, and status changes.
- Supported statuses are New, Qualified, Contacted, Replied, Won, and Lost.
- No authentication, AI workflows, scraping, email sending, external CRM, billing, Docker, or deployment work is in scope.

## Evidence on Hand

The repository contains a Next.js application and FastAPI/SQLAlchemy domain scaffold. It contains no production lead data, visual assets, testimonials, or customer claims.

## Product Principles

- Make daily lead operations immediately scannable.
- Keep records and pipeline changes persistent and explicit.
- Favor a compact, calm workspace over decorative analytics.
- Keep local setup understandable without containers.
