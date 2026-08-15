# Configuration context

Repository Beta validates deployment configuration. A valid control is a configuration copy with
the candidate keys removed while all unrelated environment inputs remain equal. Validator signals
have stable identifiers such as `CFG-4`.

The validator can emit pre-existing failures and environment-dependent failures. The same
attribution policy must apply even though the command, files, and signal format differ from the
compiler context.
