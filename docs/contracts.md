# Versioned contracts

npmctl versions each persisted document independently from the Python package. `npmctl contract list` prints the readable, writable, current, and deprecated versions. Reads may accept an older version; writes always use the current writable version. A future or unknown version fails closed and npmctl never rewrites a document during validation.

DesiredState v1 and v2 remain readable, v1 is deprecated, and v3 is the only writable desired-state contract in 0.4.0.
