# Security Policy — falsify-cookbook

## Reporting a vulnerability

Email **hello@falsify.dev** with the subject prefix `[SECURITY]`. Include a
description, the affected component and version, and a reproduction if you have
one. We aim to acknowledge within 3 working days and to say, within 10, whether
we consider it a vulnerability and what we intend to do. Do not open a public
issue for a suspected vulnerability.

There is no bug bounty. Credit is given in the changelog if you want it.

## Scope

This repository holds patterns and worked examples. It is documentation with
runnable code, not a package you install.

## Trust model

Examples that call `falsify lock`, `verify` or `hash` only read, canonicalize,
hash and compare. Examples that drive an evaluation harness (lm-eval-harness,
DeepEval, MLflow, and others) **execute** the harness and any code it is
configured to run — treat them like any script from a repository you have not
reviewed: read before running, run in an environment you would run untrusted
code in, and do not point them at credentials.

## Supported versions

Examples are kept working against the current `falsify` (PyPI) and `falsify-js`
(npm) releases named in the root README. Older combinations are not maintained.
