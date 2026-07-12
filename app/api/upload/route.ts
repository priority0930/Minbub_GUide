import { NextRequest, NextResponse } from "next/server";

export const runtime = "nodejs";

const MAX_FILE_BYTES = 25 * 1024 * 1024; // 25MB
const MAX_TEXT_CHARS = 180_000; // keep prompt payload reasonable

export async function POST(req: NextRequest) {
  try {
    const formData = await req.formData();
    const file = formData.get("file");

    if (!file || !(file instanceof File)) {
      return NextResponse.json(
        { error: "파일이 첨부되지 않았습니다." },
        { status: 400 }
      );
    }

    if (file.size > MAX_FILE_BYTES) {
      return NextResponse.json(
        { error: "파일이 너무 큽니다. 25MB 이하 파일만 업로드할 수 있습니다." },
        { status: 400 }
      );
    }

    const name = file.name || "업로드파일";
    const lowerName = name.toLowerCase();
    const arrayBuffer = await file.arrayBuffer();
    const buffer = Buffer.from(arrayBuffer);

    let text = "";
    let pageCount: number | undefined;

    if (lowerName.endsWith(".pdf") || file.type === "application/pdf") {
      const pdfParse = (await import("pdf-parse")).default;
      const data = await pdfParse(buffer);
      text = data.text;
      pageCount = data.numpages;
    } else if (
      lowerName.endsWith(".txt") ||
      file.type === "text/plain" ||
      file.type === ""
    ) {
      text = buffer.toString("utf-8");
    } else {
      return NextResponse.json(
        { error: "PDF 또는 TXT 파일만 업로드할 수 있습니다." },
        { status: 400 }
      );
    }

    text = text.replace(/\r\n/g, "\n").trim();

    if (!text) {
      return NextResponse.json(
        {
          error:
            "파일에서 텍스트를 추출하지 못했습니다. 스캔 이미지 PDF는 OCR이 필요할 수 있습니다.",
        },
        { status: 422 }
      );
    }

    let truncated = false;
    if (text.length > MAX_TEXT_CHARS) {
      text = text.slice(0, MAX_TEXT_CHARS);
      truncated = true;
    }

    return NextResponse.json({
      filename: name,
      pageCount,
      charCount: text.length,
      truncated,
      text,
    });
  } catch (err) {
    console.error("upload error", err);
    return NextResponse.json(
      { error: "파일 처리 중 오류가 발생했습니다." },
      { status: 500 }
    );
  }
}
