# Vision

## Project

langgraph-studio

## Problem Statement

Building and debugging LangGraph agents requires hand-written Python; the team needs an internal visual tool to design graphs, run them with live per-node feedback, and inspect existing LangGraph repositories, for both internal use and learning.

## High-Level Idea

A browser-based drag-and-drop LangGraph builder backed by a FastAPI service that compiles workflow JSON into LangGraph StateGraphs, streams runs over WebSocket, and can import and run existing LangGraph repos in isolated environments.

## Goals

- Visual design of LangGraph StateGraphs without boilerplate
- Offline deterministic demo (mock LLM)
- Live per-node execution feedback and run history
- Import, visualise and run existing LangGraph repos
- Learning aid for LangGraph concepts

## Non-Goals

- Public multi-tenant SaaS
- Replacing the official LangGraph Platform for production deployment
- Editing imported repo source from the canvas

## Notes

Technical direction is recorded separately (`project-specs.md`, ARCH-0001) and retains its approval status.
