---
title: Introduction
description: What is the DNS Incident Timer and why does it exist?
---

# Introduction

The **DNS Incident Timer** is a Raspberry Pi-powered desk gadget that tracks how long it's been since your last DNS-related incident. It displays the count on a bright RGB LED matrix and features a satisfying physical button to reset the counter when DNS inevitably causes problems again.

## The Problem

Every IT professional knows the pain:

- "It's not DNS"
- "There's no way it's DNS"
- "It was DNS"

DNS issues are responsible for a disproportionate number of production incidents. This project provides a fun, visible reminder of that reality.

## Features

### LED Matrix Display

A bright 32x64 RGB LED matrix shows the current count:

- **Days** since last incident (default)
- Configurable brightness
- Clear, readable from across the room

### Physical Reset Button

When DNS strikes again:

1. Press the big button
2. Hear the shameful audio clip
3. Watch the counter reset to zero
4. Contemplate your life choices

### Audio Feedback

A customizable audio clip plays when the counter resets. The default is a simple failure sound, but you can use any WAV file.

### Persistence

The timer state persists across reboots, so your shame follows you:

- Last reset time stored to disk
- Survives power outages
- Accurate count maintained

### Web Interface (Optional)

A simple web UI allows:

- Remote viewing of the current count
- Remote reset capability
- Status monitoring

## Use Cases

- **Desk decoration**: A conversation starter that displays your team's DNS track record
- **War room display**: Mount it on the wall for all to see
- **Blameless postmortem reminder**: A tangible reminder to investigate root causes
- **Team morale**: Nothing brings a team together like shared suffering

## How It Works

```
┌─────────────────┐
│  DNS Incident   │
│    Happens      │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Press Button   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐     ┌─────────────────┐
│  Play Audio     │────▶│  Reset Counter  │
└─────────────────┘     └────────┬────────┘
                                 │
                                 ▼
                        ┌─────────────────┐
                        │  Save State     │
                        └────────┬────────┘
                                 │
                                 ▼
                        ┌─────────────────┐
                        │  Update Display │
                        └─────────────────┘
```

## Next Steps

- [Hardware Requirements](/getting-started/hardware/) - What you need to build one
- [Quick Start](/getting-started/quick-start/) - Get up and running fast
