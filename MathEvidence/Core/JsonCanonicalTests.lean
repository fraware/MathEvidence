/-
Copyright (c) 2026 MathEvidence contributors. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: MathEvidence contributors
-/
import Lean.Data.Json
import MathEvidence.Core.JsonCanonical

/-!
Parity tests against `evidence/conformance/vectors/canonical_json_vectors.json`
(Python canonical module under `adapters/common` is the reference producer).
-/

namespace MathEvidence.Core.JsonCanonicalTests

open Lean
open MathEvidence.Core
open MathEvidence.Core.JsonCanonical

private def expectDigest (canonical : String) (digest : String) : Bool :=
  match Json.parse canonical with
  | .error _ => false
  | .ok j =>
    match JsonCanonical.digest j with
    | .error _ => false
    | .ok d => d.value == digest &&
        (match JsonCanonical.canonicalString j with
         | .ok s => s == canonical
         | .error _ => false)

/-- Vector `object-key-order` from conformance suite. -/
theorem vector_object_key_order :
    expectDigest "{\"a\":2,\"b\":1}"
      "sha256:d3626ac30a87e6f7a6428233b3c68299976865fa5508e4267c5415c76af7a772" = true := by
  native_decide

/-- Vector `nested` from conformance suite. -/
theorem vector_nested :
    expectDigest "{\"a\":\"q\",\"z\":[1,{\"x\":null,\"y\":true}]}"
      "sha256:50eec61bff879f09b426688576e68cb27f5bb53ac50ae26d571ff233f1e8cab4" = true := by
  native_decide

/-- Empty-object digest sanity (not in vectors file; cross-check with Python). -/
theorem empty_object_canonical :
    (match JsonCanonical.canonicalString (Json.mkObj ([] : List (String × Json))) with
     | .ok s => s == "{}"
     | .error _ => false) = true := by
  native_decide

end MathEvidence.Core.JsonCanonicalTests
