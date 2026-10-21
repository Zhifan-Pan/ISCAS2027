# Data and access

The manuscript describes the original five-language FLEURS and Common Voice 27
splits. This snapshot contains anonymous numeric features, component partitions,
reference lengths, edit counts and candidate-distance arrays. Complete-recording
lookup tables support the two-window FLEURS cases; arbitrary window edit counts
must not be summed as a substitute.

See the [candidate schema](acceptors/candidate_export_schema.json),
[availability](acceptors/candidate_availability.json) and
[gate features](r8/feature_definition.json).

Audio, reference transcripts, original client identifiers, recognizer and
language-model weights are excluded. Obtain original assets through their
providers under the applicable licenses. Numeric replay uses released exports;
recreating those exports additionally requires the original cache inputs and
mappings. Hash checks do not authenticate private sources.

The MIT license covers first-party Python code only; see
[third-party notices](../THIRD_PARTY_NOTICES.md).
