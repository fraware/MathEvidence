/-
Copyright (c) 2026 MathEvidence contributors. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: MathEvidence contributors
-/
import MathEvidence.Core.CanonicalJson
import MathEvidence.Core.EvidenceId

/-!
# Digest helpers

SHA-256 over UTF-8 bytes for request binding, following the profile in
`docs/architecture/canonical-json.md`. Lean compares digests; adapters MUST
emit the same canonical UTF-8 byte sequence before hashing.
-/

namespace MathEvidence.Core

/-- Format a 32-byte SHA-256 digest as `sha256:` ++ 64 hex chars. -/
def formatSha256Digest (digest32 : ByteArray) : Option EvidenceId :=
  if digest32.size != 32 then none
  else EvidenceId.ofWire? ("sha256:" ++ bytesToHex digest32)

/-! ## SHA-256 (FIPS 180-4), pure Lean

Used only for request/bundle binding. Not part of mathematical soundness beyond
equality of digests. -/

namespace SHA256

private def rotr (x : UInt32) (n : Nat) : UInt32 :=
  (x >>> n.toUInt32) ||| (x <<< (32 - n).toUInt32)

private def ch (x y z : UInt32) : UInt32 := (x &&& y) ^^^ ((~~~x) &&& z)
private def maj (x y z : UInt32) : UInt32 := (x &&& y) ^^^ (x &&& z) ^^^ (y &&& z)
private def bigSig0 (x : UInt32) : UInt32 := rotr x 2 ^^^ rotr x 13 ^^^ rotr x 22
private def bigSig1 (x : UInt32) : UInt32 := rotr x 6 ^^^ rotr x 11 ^^^ rotr x 25
private def smallSig0 (x : UInt32) : UInt32 := rotr x 7 ^^^ rotr x 18 ^^^ (x >>> 3)
private def smallSig1 (x : UInt32) : UInt32 := rotr x 17 ^^^ rotr x 19 ^^^ (x >>> 10)

private def K : Array UInt32 := #[
  0x428a2f98, 0x71374491, 0xb5c0fbcf, 0xe9b5dba5, 0x3956c25b, 0x59f111f1, 0x923f82a4, 0xab1c5ed5,
  0xd807aa98, 0x12835b01, 0x243185be, 0x550c7dc3, 0x72be5d74, 0x80deb1fe, 0x9bdc06a7, 0xc19bf174,
  0xe49b69c1, 0xefbe4786, 0x0fc19dc6, 0x240ca1cc, 0x2de92c6f, 0x4a7484aa, 0x5cb0a9dc, 0x76f988da,
  0x983e5152, 0xa831c66d, 0xb00327c8, 0xbf597fc7, 0xc6e00bf3, 0xd5a79147, 0x06ca6351, 0x14292967,
  0x27b70a85, 0x2e1b2138, 0x4d2c6dfc, 0x53380d13, 0x650a7354, 0x766a0abb, 0x81c2c92e, 0x92722c85,
  0xa2bfe8a1, 0xa81a664b, 0xc24b8b70, 0xc76c51a3, 0xd192e819, 0xd6990624, 0xf40e3585, 0x106aa070,
  0x19a4c116, 0x1e376c08, 0x2748774c, 0x34b0bcb5, 0x391c0cb3, 0x4ed8aa4a, 0x5b9cca4f, 0x682e6ff3,
  0x748f82ee, 0x78a5636f, 0x84c87814, 0x8cc70208, 0x90befffa, 0xa4506ceb, 0xbef9a3f7, 0xc67178f2
]

private def loadWord (block : ByteArray) (i : Nat) : UInt32 :=
  let b0 := block.get! i
  let b1 := block.get! (i + 1)
  let b2 := block.get! (i + 2)
  let b3 := block.get! (i + 3)
  (b0.toUInt32 <<< 24) ||| (b1.toUInt32 <<< 16) ||| (b2.toUInt32 <<< 8) ||| b3.toUInt32

private def storeWord (w : UInt32) : Array UInt8 :=
  #[(w >>> 24).toUInt8, (w >>> 16).toUInt8, (w >>> 8).toUInt8, w.toUInt8]

private def compress (H : Array UInt32) (block : ByteArray) : Array UInt32 :=
  Id.run do
    let mut W : Array UInt32 := Array.mkArray 64 0
    for t in [0:16] do
      W := W.set! t (loadWord block (t * 4))
    for t in [16:64] do
      let v :=
        smallSig1 (W.get! (t - 2)) + W.get! (t - 7) +
          smallSig0 (W.get! (t - 15)) + W.get! (t - 16)
      W := W.set! t v
    let mut a := H.get! 0
    let mut b := H.get! 1
    let mut c := H.get! 2
    let mut d := H.get! 3
    let mut e := H.get! 4
    let mut f := H.get! 5
    let mut g := H.get! 6
    let mut hh := H.get! 7
    for t in [0:64] do
      let T1 := hh + bigSig1 e + ch e f g + K.get! t + W.get! t
      let T2 := bigSig0 a + maj a b c
      hh := g
      g := f
      f := e
      e := d + T1
      d := c
      c := b
      b := a
      a := T1 + T2
    pure #[
      H.get! 0 + a, H.get! 1 + b, H.get! 2 + c, H.get! 3 + d,
      H.get! 4 + e, H.get! 5 + f, H.get! 6 + g, H.get! 7 + hh
    ]

/-- Pad message per SHA-256 and return consecutive 64-byte blocks. -/
private def pad (msg : ByteArray) : Array ByteArray :=
  Id.run do
    let bitLen : UInt64 := msg.size.toUInt64 * 8
    let mut buf := msg
    buf := buf.push 0x80
    while (buf.size % 64) != 56 do
      buf := buf.push 0
    for i in [0:8] do
      let shift := (7 - i) * 8
      buf := buf.push ((bitLen >>> shift.toUInt64) &&& 0xff).toUInt8
    let nblocks := buf.size / 64
    let mut blocks : Array ByteArray := #[]
    for i in [0:nblocks] do
      blocks := blocks.push (buf.extract (i * 64) ((i + 1) * 64))
    pure blocks

/-- SHA-256 hash of arbitrary bytes; returns exactly 32 bytes. -/
def hash (msg : ByteArray) : ByteArray :=
  Id.run do
    let mut H : Array UInt32 := #[
      0x6a09e667, 0xbb67ae85, 0x3c6ef372, 0xa54ff53a,
      0x510e527f, 0x9b05688c, 0x1f83d9ab, 0x5be0cd19
    ]
    for block in pad msg do
      H := compress H block
    let mut out : ByteArray := ByteArray.empty
    for w in H do
      for b in storeWord w do
        out := out.push b
    pure out

end SHA256

/-- SHA-256 of raw bytes as `EvidenceId`. -/
def sha256Bytes (msg : ByteArray) : EvidenceId :=
  match formatSha256Digest (SHA256.hash msg) with
  | some d => d
  | none => ⟨"sha256:0000000000000000000000000000000000000000000000000000000000000000"⟩

/-- SHA-256 of a Lean `String` interpreted as UTF-8 bytes via `toUTF8`. -/
def sha256String (s : String) : EvidenceId :=
  sha256Bytes s.toUTF8

/-- True when two digests are identical (request binding). -/
def digestsEqual (a b : EvidenceId) : Bool := a == b

namespace CanonicalJson

/-- SHA-256 digest of a canonical JSON string. -/
def digest (canonical : String) : EvidenceId :=
  sha256String canonical

end CanonicalJson

/-- Empty-string digest (FIPS test vector). -/
def sha256Empty : EvidenceId := sha256String ""

/-- Known SHA-256 of empty string (FIPS test vector). -/
theorem sha256Empty_eq :
    sha256Empty.value =
      "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855" := by
  native_decide

end MathEvidence.Core
