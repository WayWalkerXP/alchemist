# Alchemist Architecture Guide

## Vision

Alchemist is a metadata management platform.

## Layers

UI → Commands → Services → Persistence/External Systems.

SQLite is a cache/history store; files remain the source of truth.
