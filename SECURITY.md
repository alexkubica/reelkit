# Security and public assets

ReelKit reads local project files and renders them with Python and FFmpeg. Treat unfamiliar project JSON, media files, fonts, and dependencies as untrusted input. Review them before use and keep the runtime and media libraries updated.

## Reporting a vulnerability

If this repository exposes GitHub's **Security → Report a vulnerability** action, use it for a private report. Otherwise, open an issue requesting a private reporting channel without posting exploit details, credentials, or personal data. Include the affected version, expected impact, and a minimal synthetic reproducer when a private channel is available.

No paid support arrangement or security response deadline is implied.

## Project file boundary

- Asset references must be local paths relative to the project JSON and remain inside that project directory. Remote URLs, absolute paths, and traversal outside the project are not supported.
- Validation and rendering do not download project assets. The optional `narrate` command contacts a speech provider; its input text is sent to that provider. Use it only for text suitable for that service.
- Audio probing and decoding allow only supported local audio containers and file/pipe protocols. Streaming playlists are unsupported, including playlists stored in local files.
- Do not interpolate project values into shell commands. Use argument lists when invoking FFmpeg or other programs.
- Do not render arbitrary untrusted projects in a privileged environment. Large or malformed media can consume substantial memory, disk space, or processing time.

## Before a public release

Review tracked and staged files, including images and metadata, for secrets and personal data. Exclude `.env` files, credentials, private links, original user recordings, transcripts, generated runtime outputs, and machine-specific paths. If a credential was committed, revoke it; deleting the current file alone does not remove it from Git history.

Verify the redistribution rights for each included illustration, recording, font, and music asset. Keep credits and license terms with those assets. A tool's ability to generate or download media does not establish redistribution rights. The code license does not automatically apply to third-party assets.
