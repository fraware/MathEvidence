/-
Copyright (c) 2026 MathEvidence contributors. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: MathEvidence contributors
-/
namespace MathEvidence.Core

/-- How a theorem-level result was checked (Project Spec §7.3). -/
inductive AssuranceMode where
  /-- Ordinary Lean terms accepted by the kernel (preferred for small/medium evidence). -/
  | kernelReplay
  /-- Efficient evaluation backed by an explicit Lean soundness theorem. -/
  | verifiedReflection
  /-- Native/runtime-checked path; larger operational TCB MUST be declared. -/
  | nativeChecked
  deriving DecidableEq, Repr, Inhabited

def AssuranceMode.toWire : AssuranceMode → String
  | .kernelReplay => "kernel_replay"
  | .verifiedReflection => "verified_reflection"
  | .nativeChecked => "native_checked"

def AssuranceMode.ofWire? : String → Option AssuranceMode
  | "kernel_replay" => some .kernelReplay
  | "verified_reflection" => some .verifiedReflection
  | "native_checked" => some .nativeChecked
  | _ => none

end MathEvidence.Core
