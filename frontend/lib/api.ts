export const apiBase = process.env.NEXT_PUBLIC_API_BASE ?? "http://localhost:8000";

export function createUrl(path: string): string {
  return `${apiBase}${path}`;
}
