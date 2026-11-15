import "jsr:@supabase/functions-js/edge-runtime.d.ts";

const model = new Supabase.ai.Session("gte-small");
const encoder = new TextEncoder();
const MODEL = "gte-small/mean-normalized-v1";

// Server-to-server endpoint. Never expose this secret in a VITE_ variable.
async function authorized(value: string | null): Promise<boolean> {
  const secret = Deno.env.get("EMBEDDING_SECRET");
  if (!secret || secret.length < 32 || !value) return false;
  const digest = async (text: string) =>
    new Uint8Array(await crypto.subtle.digest("SHA-256", encoder.encode(text)));
  const [a, b] = await Promise.all([digest(value), digest(secret)]);
  return a.reduce((different, byte, i) => different | (byte ^ b[i]), 0) === 0;
}

Deno.serve(async (req) => {
  if (req.method !== "POST") return new Response("Method not allowed", { status: 405 });
  if (!(await authorized(req.headers.get("x-embedding-secret")))) {
    return new Response("Unauthorized", { status: 401 });
  }
  try {
    // Bound the streamed body before parsing; Content-Length alone is not trustworthy.
    const reader = req.body?.getReader();
    if (!reader) return new Response("Missing body", { status: 400 });
    const parts: Uint8Array[] = [];
    let size = 0;
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      size += value.length;
      if (size > 16000) {
        await reader.cancel();
        return new Response("Body too large", { status: 413 });
      }
      parts.push(value);
    }
    const bytes = new Uint8Array(size);
    let offset = 0;
    for (const part of parts) { bytes.set(part, offset); offset += part.length; }
    const { texts } = JSON.parse(new TextDecoder().decode(bytes));
    if (!Array.isArray(texts) || texts.length < 1 || texts.length > 4 ||
        texts.some((s) => typeof s !== "string" || !s.trim() || s.length > 1500)) {
      return new Response("Expected 1–4 nonempty texts, at most 1500 characters each", { status: 400 });
    }
    const embeddings: number[][] = [];
    for (const input of texts) {
      const vector = Array.from(await model.run(input, { mean_pool: true, normalize: true })) as number[];
      if (vector.length !== 384 || vector.some((v) => !Number.isFinite(v))) {
        throw new Error("Invalid model output");
      }
      embeddings.push(vector);
    }
    return Response.json({ model: MODEL, embeddings });
  } catch (error) {
    if (error instanceof SyntaxError) return new Response("Invalid JSON", { status: 400 });
    return new Response("Embedding generation unavailable", { status: 503 });
  }
});
