# The Deadlock Diner — credits and factual notes

The robot diner and dialogue are original fiction. Fork and spoon stand for exclusive resources, robots for tasks or threads. Both tasks holding one resource while waiting indefinitely for the other illustrates a two-task circular wait. Requiring every task to acquire these same resources in one consistent global order prevents this circular-wait deadlock, assuming the tasks eventually finish and release resources. This is not a claim that lock ordering fixes every concurrency bug, starvation, or all possible kinds of deadlock.

## Sources

- [Oracle Java Tutorials: Deadlock](https://docs.oracle.com/javase/tutorial/essential/concurrency/deadlock.html)
- [Oracle Berkeley DB: Locks, Blocks, and Deadlocks](https://docs.oracle.com/database/bdb181/html/gsg_txn/JAVA/blocking_deadlocks.html)

## Production

Created with the create-reel skill and the portable ReelKit renderer. Original AI-generated raster illustrations made specifically for this story with the built-in image generation tool. No downloaded stock art, music, real-person likenesses, or archival footage. Synthetic English narration using en-US-GuyNeural through the unofficial edge-tts client; Microsoft speech service. Actual provider word-boundary timings drive the burned-in English captions. Bundled Noto Sans is used under the SIL Open Font License. Artwork, voice, and captions are illustrative and do not imply endorsement by NASA, Oracle, or Microsoft.
