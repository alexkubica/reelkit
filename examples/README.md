# Offline examples

The starter copied by `reelkit init my-reel` is designed to render without speech synthesis, image-generation services, or network access. It uses original example illustrations and explicit scene durations so the first render can run on Windows, macOS, Linux, or a suitable cloud worker. Asset provenance and licenses travel with the example files.

```sh
reelkit init my-reel
reelkit validate my-reel/project.json
reelkit render my-reel/project.json --output my-reel/preview.mp4 --draft
```

Move the JSON and its asset directories together. Edit the text, scene durations, illustrations, and caption settings according to the [project format](../docs/schema.md). Add local narration files or use the optional `narrate` command when an appropriate speech service is available.

Keep generated videos and working user projects out of this public examples directory. New committed examples should be small, original, free of personal data, and redistributable; record the source and license for any third-party asset.
