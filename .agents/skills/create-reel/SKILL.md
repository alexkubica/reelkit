---
name: create-reel
description: Create or revise short illustrated videos with narration and centered subtitles using ReelKit's portable local project format and renderer.
---

# Create a reel

Produce a finished video that fits the user's audience, language, tone, and intended destination. Preserve explicit user choices over the defaults below. Read [the project schema](../../../docs/schema.md) when constructing or editing a project.

## Choose a workable production path

Run `reelkit doctor` and inspect the actual environment before promising a voice or illustration provider. ReelKit renders local files with Python and FFmpeg; image generation and speech synthesis are separate capabilities that may be absent or restricted in a cloud runtime. Use available generation tools, licensed assets, or user-provided media. Ask for a missing essential asset or requirement only when useful independent work cannot resolve it.

Research factual claims when the topic needs it, using reliable sources and retaining useful attribution in the working project. Distinguish a comedic invention from an explanation presented as fact. Check asset licenses before adding third-party images, voices, fonts, or music to a shareable project. Do not place private source material in the public repository.

## Editorial defaults

These are adjustable house preferences for a single short explainer, not universal rules for social platforms:

- Aim for roughly 25–40 seconds, with an immediate premise and one clear payoff. Choose a different length when the user's content benefits from it.
- Write spoken language in short phrases. Use sentence rhythm, emphasis, questions, and brief purposeful pauses to make narration expressive. Avoid mechanically speeding up every line or applying random pitch changes.
- Put large subtitles around the middle of the frame, in readable phrase groups with a subtle active-word highlight when reliable word timings exist. Avoid a second title that repeats the subtitles.
- Make illustrations carry the story. Vary framing, scale, viewpoints, and scene compositions; combine close-ups, visual metaphors, character action, and contextual details when useful.
- Use calm, purposeful motion within the illustration. Avoid repetitive slide layouts, screen jumps, beat bounces, and whoosh effects unless the user asks for them.
- Keep words visible long enough to read; cut according to the sentence and the visual idea rather than a fixed transition interval.

## Build and verify

1. Start a local project with `reelkit init my-reel`. Adapt its JSON and create original local assets. Keep source text, image prompts, credits, and editable material alongside the working project when useful.
2. Follow the schema for relative asset paths, scene durations, narration, phrase groups, and scene-relative word timings. Keep logical text order for right-to-left languages. Do not fabricate word-level alignment; use phrase-based timing when precise timing is unavailable.
3. Use `reelkit narrate my-reel/project.json --voice he-IL-AvriNeural --rate +15%` only if that voice and the optional network service are appropriate and available. Voice choice and rate are examples, not required settings. Existing local audio can be used instead.
4. Run `reelkit validate my-reel/project.json`, then `reelkit render my-reel/project.json --output my-reel/preview.mp4 --draft` for a quick review. Inspect frames from different compositions, transitions, and the busiest caption; listen for intelligibility and awkward pauses when playback is available.
5. Fix the observed problems, render the full output, and verify its duration, dimensions, subtitle placement, and audio. Tell the user about any material check that could not be completed.

Deliver the video with a direct file link and a concise description. Keep reusable source material if requested. Local creation does not itself authorize publishing or sending the video elsewhere; an explicit user request to publish is sufficient authorization for the named destination.
