import { NextRequest, NextResponse } from "next/server";
import { getAnthropicClient, CHAT_MODEL } from "@/lib/anthropic";
import { SYSTEM_PROMPT, SESSION_KICKOFF_HINT } from "@/lib/systemPrompt";

export const runtime = "nodejs";

type ChatMessage = {
  role: "user" | "assistant";
  content: string;
};

type Material = {
  filename: string;
  text: string;
  charCount: number;
  truncated: boolean;
};

export async function POST(req: NextRequest) {
  try {
    const body = await req.json();
    const messages: ChatMessage[] = body.messages ?? [];
    const material: Material | null = body.material ?? null;
    const isFirstTurnWithMaterial: boolean = Boolean(body.isFirstTurnWithMaterial);

    if (!Array.isArray(messages) || messages.length === 0) {
      return NextResponse.json(
        { error: "메시지가 비어 있습니다." },
        { status: 400 }
      );
    }

    let system = SYSTEM_PROMPT;
    if (material?.text) {
      system += `\n\n# 업로드된 학습 자료\n파일명: ${material.filename}\n${
        material.truncated
          ? "(참고: 자료가 길어 앞부분 일부만 전달됨. 이후 후속 업로드로 이어질 수 있음)\n"
          : ""
      }<document>\n${material.text}\n</document>`;
      if (isFirstTurnWithMaterial) {
        system += `\n\n${SESSION_KICKOFF_HINT}`;
      }
    }

    const client = getAnthropicClient();
    const response = await client.messages.create({
      model: CHAT_MODEL,
      max_tokens: 4096,
      system,
      messages: messages.map((m) => ({
        role: m.role,
        content: m.content,
      })),
    });

    const textBlock = response.content.find((block) => block.type === "text");
    const reply = textBlock && "text" in textBlock ? textBlock.text : "";

    return NextResponse.json({ reply });
  } catch (err) {
    console.error("chat error", err);
    const message =
      err instanceof Error ? err.message : "챗봇 응답 중 오류가 발생했습니다.";
    return NextResponse.json({ error: message }, { status: 500 });
  }
}
