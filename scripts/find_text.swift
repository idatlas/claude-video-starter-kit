// Find every line of text in an image, with where it is. Runs on your Mac (Apple's Vision), offline.
//   swift scripts/find_text.swift shot.png            -> JSON lines: {"text", "x", "y", "w", "h"} (fractions, top-left origin)
// Used to spot names, emails and keys that need blurring before a screenshot or video is shared.
import Foundation
import Vision
import AppKit

let path = CommandLine.arguments.count > 1 ? CommandLine.arguments[1] : ""
guard let img = NSImage(contentsOfFile: path), let cg = img.cgImage(forProposedRect: nil, context: nil, hints: nil) else {
    FileHandle.standardError.write("Can't open image: \(path)\n".data(using: .utf8)!); exit(1)
}
let req = VNRecognizeTextRequest()
req.recognitionLevel = .accurate
req.usesLanguageCorrection = false
try VNImageRequestHandler(cgImage: cg, options: [:]).perform([req])
var out: [[String: Any]] = []
for obs in req.results ?? [] {
    guard let c = obs.topCandidates(1).first else { continue }
    let b = obs.boundingBox
    out.append(["text": c.string, "x": round(b.minX * 10000) / 10000, "y": round((1 - b.maxY) * 10000) / 10000,
                "w": round(b.width * 10000) / 10000, "h": round(b.height * 10000) / 10000])
}
let data = try JSONSerialization.data(withJSONObject: out, options: [])
print(String(data: data, encoding: .utf8)!)
