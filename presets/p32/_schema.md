# p32 preset schema (F7 generalized preset renderer)
{genre, world: "volt", res: [720,1280], fps: 30, dur: 12.0,
 hook: {word, sub, src_t}, beats: [{t, dur, op, src_t, ...ops params}],
 listicle: {items[], values{}}, caption: {text, t}, endcard: {word, pill},
 audio: {foley: [{t, kind, gain}], bed_gain},
 clip: {path, dur, energy_reframe: true}}
OPS: hook_slam | footage | video_in_card | listicle | shrink_card | endcard
World census: volt-only (B8 rule). No internal labels. All volt accents (F1).
