# Request for an independent Ceremony Zero co-custodian

Ceremony Zero is a small public experiment in blind evaluation. Its first two
versions demonstrated replayable chronology and exposed several real protocol
failures, including early label disclosure. The current status is NO-GO.

We are looking for one independent person or organization to test the missing
property rather than endorse the project.

## What we would ask you to do

1. Review a frozen, small Python protocol and either reject it or agree to act
   as label custodian.
2. Generate or hold three or more tiny deterministic toy policies and their
   labels after the auditor is frozen.
3. Keep the policies' hidden semantics, labels, and a random commitment nonce
   outside the author's access until verdicts are finalized.
4. Run the frozen auditor in your environment, publish a FINALIZE receipt, and
   then reveal the subjects and labels for public replay.
5. Publish every failure. A broken run is useful evidence.

## What this is not

- no real model checkpoint;
- no private production data;
- no claim that the toy auditor detects general AI backdoors;
- no request to endorse a safety result; and
- no need to trust the current implementation—it is explicitly marked NO-GO.

The intended deliverable is one independently custodied transcript or a clear
reason the protocol should not run. Either outcome closes a real uncertainty.
