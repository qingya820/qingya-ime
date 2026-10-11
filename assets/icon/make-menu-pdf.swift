import Foundation
import CoreGraphics
import CoreText

// 生成青崖菜单栏模板图标：22pt 见方 PDF，「山」字占页面约 40%，严格居中。
// 模板图系统只取 alpha，颜色任意（用黑色）。矢量，任意 DPI 清晰。
let pageSize = CGSize(width: 22, height: 22)
let url = URL(fileURLWithPath: CommandLine.arguments[1])
guard let ctx = CGContext(url as CFURL, mediaBox: nil, nil) else { fatalError("无法创建 PDF 上下文") }

var box = CGRect(origin: .zero, size: pageSize)
ctx.beginPDFPage([kCGPDFContextMediaBox: NSData(bytes: &box, length: MemoryLayout<CGRect>.size)] as CFDictionary)

let font = CTFontCreateWithName("PingFangSC-Semibold" as CFString, 10.0, nil) // 10pt 字面，墨迹实测约占页面 40%
var glyph = CGGlyph()
var scalar: UTF16.CodeUnit = 0x5C71 // 山
CTFontGetGlyphsForCharacters(font, &scalar, &glyph, 1)
var position = CGPoint.zero
// 按字形墨迹边界（非字体行高）居中
var advance = CGSize.zero
CTFontGetAdvancesForGlyphs(font, .horizontal, &glyph, &advance, 1)
let bbox = CTFontGetBoundingRectsForGlyphs(font, CTFontOrientation(rawValue: 0)!, &glyph, nil, 1)
position.x = (pageSize.width - bbox.width) / 2 - bbox.minX
position.y = (pageSize.height - bbox.height) / 2 - bbox.minY
ctx.setFillColor(gray: 0, alpha: 1)
CTFontDrawGlyphs(font, &glyph, &position, 1, ctx)

ctx.endPDFPage()
ctx.closePDF()
print("written \(url.path)")
